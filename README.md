# Gazprom_Xakaton

Проект для анализа качества CSV данных, реализованный с использованием FastAPI, Celery и Docker.

## Структура проекта

- **fastapi/** – веб-приложение на [FastAPI](https://fastapi.tiangolo.com/) для загрузки CSV файла, анализа данных и отображения результатов:
  - `app.py` – основной файл приложения.
  - `config.py` – загрузка и проверка переменных окружения.
  - `templates/` – HTML-шаблоны, например, `upload.html` и `results.html`.
  - `static/` – статические файлы, такие как `styles.css`.
  - `Dockerfile` и `entrypoint.sh` – файлы для контейнеризации.

- **celery/** – сервис для обработки фоновых задач:
  - `app.py` – настройка Celery.
  - `tasks.py` – примеры задач для обработки данных.
  - `producer.py` и `api.py` – отправка и получение задач.
  - `Dockerfile` и `entrypoint.sh` – файлы для контейнеризации.

- **shared/** – общие файлы и каталоги, используемые для обмена данными между сервисами.

- Другие файлы:
  - `docker-compose.yaml` – конфигурация для развёртывания всех сервисов с помощью Docker.
  - `.env.example` – пример файла с переменными окружения.
  - `LICENSE` – лицензия проекта.
  - Архитектурные схемы – `architecture.drawio` и `architecture2.drawio`.

## Технологии

- [FastAPI](https://fastapi.tiangolo.com/)
- [Celery](https://docs.celeryq.dev/en/stable/)
- [Docker / Docker Compose](https://docs.docker.com/compose/)
- [Pandas](https://pandas.pydata.org/)
- [Plotly](https://plotly.com/python/)

## Использование

Проект предназначен для анализа CSV данных с использованием FastAPI для веб-интерфейса и Celery для фоновой обработки задач. Детали запуска зависят от внешних настроек (например, сертификатов для сервера).  
Для подробностей по настройке среды смотрите документацию проекта и соответствующие инструкции для каждого сервиса.

## Архитектура

В проекте включены схемы, визуализирующие взаимодействие компонентов:
- `architecture.drawio`
- `architecture2.drawio`

## Лицензия

Проект распространяется под Apache License 2.0.