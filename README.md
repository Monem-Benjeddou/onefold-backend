# Onefold

The web app and API for Onefold: a platform that teaches people to ship complete products,
from idea to production. Builders follow a path of stations (Idea → Product →
UX/UI → System → Build → Test → Deploy → Run → Iterate), build their own project
with their own tools, and Onefold verifies each step.

**API:** Django 5.2 · Django REST Framework · PostgreSQL 16 · Redis · Celery
**Web:** Next.js 16 · React 19 · Tailwind CSS 4 (in `web/`)

## Run it

```bash
cp .env.example .env        # set SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
```

- **App: http://localhost:3000**
- API: http://localhost:8000 · API docs: http://localhost:8000/api/docs/ · Health: /health/

The `api` container migrates the database and loads the learning content on
start. While `DEBUG=1`, sign-in emails (with the link) print in its logs:

```bash
docker compose logs -f api      # look for http://localhost:3000/auth/verify?token=...
docker compose exec api python manage.py createsuperuser   # for /admin/
```

### Web app without Docker

```bash
cd web
npm install
BACKEND_URL=http://localhost:8000 npm run dev    # http://localhost:3000
```

The browser only talks to the web app. Tokens live in httpOnly cookies, and
`/api/proxy/*` forwards calls to the API, so there's no CORS setup and no
token in page scripts.

### API without Docker

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DEBUG=1              # no POSTGRES_DB → SQLite, no REDIS_URL → in-memory cache
python manage.py migrate
python manage.py sync_content --publish
python manage.py runserver
```

Checks run on Celery, so "Check my work" needs Redis and
`celery -A config worker -l info`, or `CELERY_TASK_ALWAYS_EAGER=1` to run them inline.

## Test and lint

```bash
pytest                       # SQLite, no services needed
TEST_USE_SQLITE=0 pytest     # against the Postgres in POSTGRES_*
ruff check . && ruff format --check .
```

## How it's organised

```
web/               Next.js app: landing, sign-in, onboarding, dashboard,
                   path, steps + "Check my work", project, ship moment
config/            settings (all env-driven), urls, celery
apps/
  core/            base model (UUID + timestamps), /health/
  accounts/        email users, passwordless magic-link sign-in, JWT
  learning/        paths, stations, steps, enrollment, progress
  projects/        the builder's product: repo, live URL, ownership token
  verification/    "Check my work": check runs, executors, SSRF-safe HTTP
content/           learning paths as Markdown + YAML (see content/README.md)
MVP_PLAN.md        product, UX and engineering plan for the MVP
```

## API at a glance

| Method | Path | What it does |
|--------|------|--------------|
| POST | `/api/v1/auth/magic-link/` | Email a sign-in link (always 202) |
| POST | `/api/v1/auth/magic-link/verify/` | Exchange the link's token for JWTs |
| POST | `/api/v1/auth/token/refresh/` | Rotate tokens |
| POST | `/api/v1/auth/logout/` | Revoke a refresh token |
| GET/PATCH/DELETE | `/api/v1/auth/me/` | The signed-in builder |
| GET | `/api/v1/learning/paths/current/` | Path outline |
| GET/POST | `/api/v1/learning/enrollment/` | Progress / enroll |
| GET/PATCH | `/api/v1/learning/enrollment/steps/{slug}/` | Step content, save position |
| POST | `/api/v1/learning/enrollment/steps/{slug}/start/` `…/complete/` | Move through steps |
| GET/POST | `/api/v1/projects/` | The builder's projects |
| GET/POST | `/api/v1/projects/{id}/checks/` | Check history / "Check my work" |
| GET | `/api/v1/checks/{id}/` | Poll one check |

Send `Authorization: Bearer <access>` on everything except sign-in.
