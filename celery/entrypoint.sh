#!/bin/sh
set -e


uvicorn api:app --host 0.0.0.0 --port 8000 &


celery -A celery.app worker --loglevel=info --concurrency=4