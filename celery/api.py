import os
from fastapi import FastAPI, HTTPException, Query
from producer import push

app = FastAPI()

UPLOAD_DIR = "/app/"

@app.get("/test")
async def test():
    return os.listdir(UPLOAD_DIR)


@app.post("/process/")
async def process_file(filename: str = Query(..., description="Имя файла, который заранее загружен в общий каталог")):
    file_path = os.path.join(UPLOAD_DIR, filename)
    print(os.listdir(UPLOAD_DIR))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Файл не найден в общем каталоге.")
    
    try:
        result = push(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"result": result, "message": f"Файл {filename} обработан"}