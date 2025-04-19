FROM --platform=linux/amd64 python:3.12-slim as build

# Переназначим рабочую папку
WORKDIR /fastapi

# Скопировать только requirements (чтобы не пересобирать pip при каждом изменении кода)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Скопировать весь оставшийся код
COPY . .

# Сделать entrypoint.sh исполняемым (если нужно)
RUN chmod +x entrypoint.sh

# Запуск при старте контейнера

# Запуск при старте контейнера
ENTRYPOINT ["python", "./app.py"]