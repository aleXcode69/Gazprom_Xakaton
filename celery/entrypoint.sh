#!/bin/sh
# Запускаем celery worker в фоне, скрывая его логи
celery -A app worker --loglevel=info --concurrency=4 > /dev/null 2>&1 &
# Запускаем uvicorn в фореграунде – его логи будут выводиться в терминал
uvicorn api:app --host 0.0.0.0 --port 8000