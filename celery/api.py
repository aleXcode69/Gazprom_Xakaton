import os
from fastapi import FastAPI, HTTPException, Query
from producer import push

app = FastAPI()

UPLOAD_DIR = "/app/data/"

def is_path_inside_directory(child_path, parent_directory):
    parent_directory = os.path.abspath(parent_directory)
    child_path = os.path.abspath(child_path)
    return os.path.commonpath([child_path]) == parent_directory or os.path.commonpath([child_path, parent_directory]) == parent_directory

@app.get("/test")
async def test():
    return os.listdir(UPLOAD_DIR)

@app.post("/process/")
async def process_file(filename: str = Query(..., description="Имя файла, который заранее загружен в общий каталог")):
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Проверка, что итоговый путь находится внутри UPLOAD_DIR
    if not is_path_inside_directory(file_path, UPLOAD_DIR):
        raise HTTPException(status_code=400, detail="Недопустимый путь к файлу.")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail="Файл не найден в общем каталоге.")
    
    print(os.listdir(UPLOAD_DIR))
    
    try:
        result = push(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"result": result, "message": f"Файл {filename} обработан"}