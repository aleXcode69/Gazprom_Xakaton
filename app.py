from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import io
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import os

app = FastAPI()

# Настройка статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Глобальные переменные для хранения данных
processed_data = {}
current_analysis = {}

def find_partial_duplicates(df: pd.DataFrame, column: str) -> Tuple[int, int, List[pd.DataFrame]]:
    """Находит частичные дубликаты по всем столбцам кроме указанного"""
    other_columns = [col for col in df.columns if col != column]

    if not other_columns:
        return 0, 0, []

    # Группируем по всем столбцам кроме указанного
    grouped = df.groupby(other_columns)

    duplicate_groups = 0
    duplicate_rows = 0
    samples = []

    for name, group in grouped:
        if len(group) > 1:
            duplicate_groups += 1
            duplicate_rows += len(group)

            # Сохраняем первые 3 группы для примеров
            if duplicate_groups <= 3:
                samples.append(group.head(3))

    return duplicate_groups, duplicate_rows, samples

@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_csv(request: Request, file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    except Exception as e:
        return f"Ошибка при чтении файла: {str(e)}"

    # Находим 5 столбцов с наибольшей уникальностью
    uniqueness = {col: df[col].nunique() for col in df.columns}
    top_columns = sorted(uniqueness, key=uniqueness.get, reverse=True)[:5]

    # Анализ частичных дубликатов для каждого из топ-столбцов
    partial_duplicates_info = []
    partial_duplicates_samples = []

    for column in top_columns:
        groups, rows, samples = find_partial_duplicates(df, column)
        partial_duplicates_info.append({
            "column": column,
            "duplicate_groups": groups,
            "duplicate_rows": rows
        })

        if samples:
            partial_duplicates_samples.extend(samples)

    analysis = {
        "request": request,
        "filename": file.filename,
        "file_size_kb": round(len(contents) / 1024, 2),
        "row_count": len(df),
        "col_count": len(df.columns),
        "total_missing": df.isnull().sum().sum(),
        "rows_with_missing": df.isnull().any(axis=1).sum(),
        "missing_values": [(col, df[col].isnull().sum(), df[col].isnull().mean() * 100)
                         for col in df.columns],
        "full_duplicates": df.duplicated().sum(),
        "top_columns": top_columns,
        "partial_duplicates_info": partial_duplicates_info,
        "partial_duplicates_samples": partial_duplicates_samples[:3],
        "column_stats": [],
        "processed": False
    }

    # Сохраняем данные для обработки
    processed_data[file.filename] = {
        "original": df.copy(),
        "processed": df.copy()
    }
    current_analysis[file.filename] = analysis

    # Собираем статистику по столбцам
    for col in df.columns:
        dtype = str(df[col].dtype)
        unique = df[col].nunique()
        sample = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else "N/A"

        if isinstance(sample, str) and len(sample) > 50:
            sample = sample[:50] + "..."

        analysis["column_stats"].append((col, dtype, unique, sample))

    return templates.TemplateResponse("results.html", analysis)

@app.post("/process_duplicates", response_class=HTMLResponse)
async def process_duplicates(
        request: Request,
        filename: str = Form(...),
        action: str = Form(...),
        column: Optional[str] = Form(None),
        merge_strategy: Optional[str] = Form(None)
):
    if filename not in processed_data:
        return "Файл не найден"

    df = processed_data[filename]["processed"]
    analysis = current_analysis[filename]
    analysis["request"] = request

    if action == "remove_full":
        # Удаляем полные дубликаты
        df = df.drop_duplicates()
        processed_data[filename]["processed"] = df
        analysis["full_duplicates"] = 0
        analysis["processed"] = True

    elif action == "merge_partial" and column:
        # Объединяем частичные дубликаты по указанному столбцу
        other_columns = [col for col in df.columns if col != column]

        if other_columns:
            if merge_strategy == "first":
                df = df.groupby(other_columns, as_index=False).first()
            elif merge_strategy == "last":
                df = df.groupby(other_columns, as_index=False).last()
            elif merge_strategy == "concat":
                df = df.groupby(other_columns)[column].apply(lambda x: ', '.join(map(str, x))).reset_index()

            processed_data[filename]["processed"] = df
            analysis["processed"] = True

            # Обновляем статистику частичных дубликатов
            new_info = []
            for col_info in analysis["partial_duplicates_info"]:
                if col_info["column"] == column:
                    groups, rows, _ = find_partial_duplicates(df, column)
                    new_info.append({
                        "column": column,
                        "duplicate_groups": groups,
                        "duplicate_rows": rows
                    })
                else:
                    new_info.append(col_info)

            analysis["partial_duplicates_info"] = new_info

    return templates.TemplateResponse("results.html", analysis)

@app.post("/download")
async def download_file(filename: str = Form(...)):
    if filename not in processed_data:
        return "Файл не найден"

    df = processed_data[filename]["processed"]
    stream = io.StringIO()
    df.to_csv(stream, index=False)

    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=processed_{filename}"
        }
    )

    return response

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)