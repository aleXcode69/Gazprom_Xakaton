from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import io
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import os
import plotly.graph_objects as go
import json
import networkx as nx
import requests
from config import OpenRouterConfig

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

processed_data = {}
current_analysis = {}


def make_openrouter_request(url: str, data: dict) -> Optional[dict]:
     for attempt in range(OpenRouterConfig.MAX_RETRIES):
         try:
             headers = {
                 "Authorization": f"Bearer {OpenRouterConfig.get_current_key()}",
                 "Content-Type": "application/json"
             }
             
             response = requests.post(url, headers=headers, json=data)
             response.raise_for_status()
             return response.json()
             
         except requests.exceptions.RequestException as e:
             if attempt < OpenRouterConfig.MAX_RETRIES - 1:
                 # Ротируем ключ при ошибке
                 OpenRouterConfig.rotate_key()
                 continue
             raise e


async def get_ai_response(messages):
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages
    }

    try:
        response = make_openrouter_request(
            "https://openrouter.ai/api/v1/chat/completions",
            data
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception(f"Ошибка API: {str(e)}")


def find_partial_duplicates(df: pd.DataFrame, column: str) -> Tuple[int, int, List[pd.DataFrame], List]:
    other_columns = [col for col in df.columns if col != column]
    if not other_columns:
        return 0, 0, [], []

    grouped = df.groupby(other_columns)
    duplicate_groups = 0
    duplicate_rows = 0
    samples = []
    duplicate_values = []

    for name, group in grouped:
        if len(group) > 1:
            duplicate_groups += 1
            duplicate_rows += len(group)
            duplicate_values.extend(group[column].unique().tolist())
            if duplicate_groups <= 5:
                samples.append(group.head(5))

    duplicate_values = list(set(duplicate_values))
    return duplicate_groups, duplicate_rows, samples, duplicate_values


def create_quality_chart(df: pd.DataFrame) -> str:
    stats = []
    for col in df.columns:
        stats.append({
            'column': col,
            'unique': df[col].nunique(),
            'missing': df[col].isnull().sum(),
            'dtype': str(df[col].dtype)
        })

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[s['column'] for s in stats],
        y=[s['unique'] for s in stats],
        name='Уникальные',
        marker_color='#4CAF50'
    ))
    fig.add_trace(go.Bar(
        x=[s['column'] for s in stats],
        y=[s['missing'] for s in stats],
        name='Пропущенные',
        marker_color='#F44336'
    ))
    fig.update_layout(
        barmode='group',
        title='Качество данных по столбцам',
        xaxis_title='Столбцы',
        yaxis_title='Количество',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified'
    )
    return fig.to_json()


def create_unpopular_graph(df: pd.DataFrame) -> str:
    # Находим 5 столбцов с наименьшей уникальностью
    uniqueness = {col: df[col].nunique() for col in df.columns}
    least_unique_cols = sorted(uniqueness, key=uniqueness.get)[:5]

    # Создаем граф
    G = nx.Graph()

    # Добавляем узлы для столбцов
    for col in least_unique_cols:
        G.add_node(f"col_{col}", label=col, type='column', size=20, color='#3498db')

        # Добавляем 3 наименее уникальных значения
        least_common = df[col].value_counts().nsmallest(3)
        for val, count in least_common.items():
            val_str = str(val)[:20] + ('...' if len(str(val)) > 20 else '')
            G.add_node(f"val_{col}_{val_str}",
                       label=f"{val_str} ({count})",
                       type='value',
                       size=10 + count * 2,
                       color='#e74c3c')
            G.add_edge(f"col_{col}", f"val_{col}_{val_str}", weight=count)

    # Позиционирование узлов
    pos = nx.spring_layout(G, k=0.5, iterations=50)

    # Создаем Plotly figure
    fig = go.Figure()

    # Добавляем ребра
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode='lines',
            line=dict(width=1, color='#95a5a6'),
            hoverinfo='none',
            showlegend=False
        ))

    # Добавляем узлы
    for node in G.nodes():
        x, y = pos[node]
        node_data = G.nodes[node]
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(
                size=node_data['size'],
                color=node_data['color'],
                line=dict(width=2, color='DarkSlateGrey')
            ),
            text=node_data['label'],
            textposition="middle center",
            hoverinfo='text',
            name=node_data['label'],
            textfont=dict(
                size=12,
                color='black'
            )
        ))

    # Настраиваем layout
    fig.update_layout(
        title='Граф наименее уникальных значений',
        showlegend=False,
        hovermode='closest',
        margin={'b': 40, 'l': 40, 'r': 40, 't': 80},
        xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
        yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
        height=600,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig.to_json()


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

    chart_json = create_quality_chart(df)
    unpopular_graph_json = create_unpopular_graph(df)

    uniqueness = {col: df[col].nunique() for col in df.columns}
    top_columns = sorted(uniqueness, key=uniqueness.get, reverse=True)[:5]
    partial_duplicates_info = []

    for column in top_columns:
        groups, rows, samples, dup_values = find_partial_duplicates(df, column)
        partial_duplicates_info.append({
            "column": column,
            "duplicate_groups": groups,
            "duplicate_rows": rows,
            "duplicate_values": dup_values,
            "samples": samples[:3]
        })

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
        "column_stats": [],
        "processed": False,
        "quality_chart": chart_json,
        "unpopular_graph": unpopular_graph_json
    }

    processed_data[file.filename] = {
        "original": df.copy(),
        "processed": df.copy()
    }
    current_analysis[file.filename] = analysis

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
        merge_strategy: Optional[str] = Form(None),
        custom_value: Optional[str] = Form(None)
):
    if filename not in processed_data:
        return "Файл не найден"

    df = processed_data[filename]["processed"]
    analysis = current_analysis[filename]
    analysis["request"] = request

    if action == "remove_full":
        df = df.drop_duplicates()
        processed_data[filename]["processed"] = df
        analysis["full_duplicates"] = 0
        analysis["processed"] = True
    elif action == "merge_partial" and column:
        other_columns = [col for col in df.columns if col != column]
        if other_columns:
            if merge_strategy == "first":
                df = df.groupby(other_columns, as_index=False).first()
            elif merge_strategy == "last":
                df = df.groupby(other_columns, as_index=False).last()
            elif merge_strategy == "concat":
                df = df.groupby(other_columns)[column].apply(lambda x: ', '.join(map(str, x))).reset_index()
            elif merge_strategy == "custom" and custom_value:
                groups, _, _, dup_values = find_partial_duplicates(df, column)
                if custom_value in dup_values:
                    df = df.groupby(other_columns, as_index=False).apply(
                        lambda x: x[x[column] == custom_value].head(1) if any(x[column] == custom_value) else x.head(1)
                    ).reset_index(drop=True)

            processed_data[filename]["processed"] = df
            analysis["processed"] = True
            analysis["quality_chart"] = create_quality_chart(df)
            analysis["unpopular_graph"] = create_unpopular_graph(df)

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


@app.post("/ask_ai")
async def ask_ai(
    request: Request,
    filename: str = Form(...),
    column: str = Form(...),
    message: Optional[str] = Form(None)
):
    if filename not in processed_data:
        return {"error": "Файл не найден"}

    df = processed_data[filename]["processed"]
    
    # Получаем примеры дубликатов для указанного столбца
    other_columns = [col for col in df.columns if col != column]
    grouped = df.groupby(other_columns)
    samples = []
    
    for name, group in grouped:
        if len(group) > 1:
            samples.append(group.head(5))
            if len(samples) >= 3:  # Берем максимум 3 примера
                break

    if not message:
        # Формируем первое сообщение
        prompt = f"""С тобой общается оператор по данным. Перед ним стоит выбор - объединять ли частичные дубликаты данных, у которых столбец {column} разное, а все остальные столбцы совпадают. 
1. Подскажи оператору, стоит ли такие данные обьединять и объясни почему (реши это на основании названия поля и содержания столбцов)
2. Укажи, какое поле из отличающихся оставить (первое, последнее, или выбери нужное из данных, которое я тебе скину) и также объясни почему)
Данные прилагаю: {samples}"""

        messages = [{"role": "user", "content": prompt}]
    else:
        messages = [{"role": "user", "content": message}]

    try:
        response = await get_ai_response(messages)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    os.makedirs("static", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)