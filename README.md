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

| What | Where |
|------|-------|
| **App** | **http://localhost:3000** |
| Inbox (every email the app sends) | http://localhost:8025 |
| Django admin | http://localhost:8000/admin/ |
| API docs | http://localhost:8000/api/docs/ |

On start, the `api` container migrates the database, loads the learning content
and seeds demo accounts. Nothing needs the logs:

- **Demo accounts:** the login page has a "Sign in as…" panel (development only).
  One click signs you in. Or use the email and password `onefold`.
- **Real accounts:** "Create an account" works for any email. Confirmation,
  password-reset and sign-in emails land in the **local inbox** (Mailpit), and
  the app links to it after sending one.

| Account | Stage |
|---------|-------|
| `new@onefold.local` | Signed up, goes through onboarding |
| `ada@onefold.local` | Just started (station 1) |
| `grace@onefold.local` | At Deploy, with a failed check |
| `linus@onefold.local` | Shipped: live URL and the "It's live." screen |
| `admin@onefold.local` | Django admin only (password `SEED_ADMIN_PASSWORD`, default `onefold`) |

`docker compose exec api python manage.py seed --reset` rebuilds the demo accounts.
Set `SEED_DEMO_DATA=0` to skip seeding. Demo sign-in and the seeder refuse to run with `DEBUG=0`.

### Signing in

| Method | Notes |
|--------|-------|
| Email + password | Sign-up sends a confirmation link; the app works right away and shows a banner until confirmed. 5 wrong passwords lock that email for 15 minutes. |
| Forgot password | Emailed link, single use, 30 minutes. Resetting signs out every other device. Also how link-only or GitHub accounts set a password. |
| Email sign-in link | Single use, 15 minutes. |
| GitHub / Google | Shown when `GITHUB_CLIENT_ID`/`_SECRET` (or `GOOGLE_…`) are set. Callback URL: `FRONTEND_URL/api/auth/oauth/<provider>/callback`. Accounts link by verified email. |

Every sign-in creates a device session (`/api/v1/auth/sessions/`), which can be
revoked one by one or all at once. Sign-ins, failures, lockouts, resets and
sign-outs are recorded in the admin under *Sign-in events*.

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
(cd web && npm run typecheck && npm run build)
```

End-to-end tests drive a real browser against the running stack (sign-up,
onboarding with a refresh halfway, password reset through the inbox, an
expired session mid-form, phone layout):

```bash
docker compose up -d --build
cd e2e && npm ci && npx playwright install chromium
npx playwright test          # WEB_URL / MAILPIT_URL default to localhost
```

CI runs all of it: lint, migrations, content, API tests on PostgreSQL, web
typecheck and build, the end-to-end suite, and both images.

## How it's organised

```
web/               Next.js app: landing, sign-in/sign-up/reset, onboarding,
                   dashboard, path, steps + "Check my work", project, ship moment
e2e/               Playwright end-to-end tests
config/            settings (all env-driven), urls, celery
apps/
  core/            base model (UUID + timestamps), /health/
  accounts/        users, password + magic-link + GitHub/Google sign-in, JWT,
                   device sessions, lockout, sign-in audit
  workspace/       onboarding (one transaction, saved drafts) and /workspace
  learning/        paths, stations, steps, enrollment, progress
  projects/        the builder's product: repo, live URL, ownership token
  verification/    "Check my work": check runs, executors, SSRF-safe HTTP
content/           learning paths as Markdown + YAML (see content/README.md)
MVP_PLAN.md        product, UX and engineering plan for the MVP
docs/REVIEW_AND_PLAN.md   state review and the phased plan (Phase 0 + 1 done)
```

## API at a glance

| Method | Path | What it does |
|--------|------|--------------|
| GET | `/api/v1/auth/config/` | Which sign-in methods are on |
| POST | `/api/v1/auth/register/` · `/login/` | Email + password |
| POST | `/api/v1/auth/password/forgot/` · `/reset/` · `/change/` | Password recovery and change |
| POST | `/api/v1/auth/magic-link/` · `/magic-link/verify/` | Email sign-in link |
| POST | `/api/v1/auth/email/verify/` · `/email/resend/` | Confirm the email address |
| POST | `/api/v1/auth/oauth/{github,google}/start/` · `/callback/` | GitHub / Google |
| POST | `/api/v1/auth/token/refresh/` · `/logout/` | Rotate tokens / sign this device out |
| GET/DELETE | `/api/v1/auth/sessions/` · `/sessions/{id}/` | Signed-in devices |
| GET/PATCH/DELETE | `/api/v1/auth/me/` | The signed-in builder |
| GET | `/api/v1/workspace/` | Builder + enrollment + project in one call |
| GET/POST | `/api/v1/onboarding/` · PUT `/onboarding/draft/` | Onboarding state, finish, save answers |
| GET | `/api/v1/learning/paths/current/` | Path outline |
| GET/POST | `/api/v1/learning/enrollment/` | Progress / enroll |
| GET/PATCH | `/api/v1/learning/enrollment/steps/{slug}/` | Step content, save position |
| POST | `/api/v1/learning/enrollment/steps/{slug}/start/` `…/complete/` | Move through steps |
| GET/POST | `/api/v1/projects/` | The builder's projects |
| GET/POST | `/api/v1/projects/{id}/checks/` | Check history / "Check my work" |
| GET | `/api/v1/checks/{id}/` | Poll one check |

Send `Authorization: Bearer <access>` on everything except sign-in. Errors carry a `code` and a `request_id` (also in the `X-Request-ID` header).
