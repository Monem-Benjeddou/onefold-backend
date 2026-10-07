# Noev Backend Starter

Minimal Django + DRF starter extracted from kolct-api, with environment-based settings, OpenAPI docs, and Docker support.

## Quickstart

1. Create environment file

```
# If .env.example is not present, copy and adjust from this section in README
# or create one manually with the variables used in config/settings.py
```

2. Install dependencies and run migrations

```
python -m venv .venv && .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://localhost:8000/api/docs/

## Docker

```
cp .env.example .env      # then set SECRET_KEY and DATABASE_PASSWORD
docker compose up --build
```

The API is on http://localhost:8009 (`API_PORT`). The root `docker-compose.yml`
includes `docker/docker-compose.yml`; `make up` runs the same stack.

Load the learning content once the stack is up:

```
docker compose exec nevo-backend python manage.py migrate
docker compose exec nevo-backend python manage.py sync_content --publish
```

## Features

- Django 5, DRF, CORS, Spectacular (OpenAPI)
- Health endpoint at /health/
- API root at /api/
- Swagger UI at /api/docs/
- Env-driven settings with SQLite default, Postgres optional
- Nginx, Gunicorn, Redis, Postgres compose

## Project layout

- config: settings, urls, wsgi/asgi
- noev: example app with root endpoint
- docker: nginx/postgres/redis configs
