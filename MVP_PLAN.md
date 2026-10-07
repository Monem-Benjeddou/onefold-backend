# Onefold — MVP Plan

> Working name: **Onefold** (see Brand Guidelines 1.0). Status: draft for founder review.
> Owner: product · Last updated: 2026-10-07

---

## 0. TL;DR

- **The bet.** Someone with an idea will follow one guided, project-based path and **actually put a real product on the internet** if we remove three things that stop them: not knowing what comes next, not knowing whether what they did is right, and the loneliness of the hard part (deploying).
- **The MVP.** One path, *Ship your first full-stack product*: 9 stations (Idea → Iterate), about 45 steps. The learner builds **their own** project with **their own** tools (editor, GitHub, a hosting provider). Onefold supplies the map, the next step, **automated verification** (GitHub plus a live-URL check), an **AI reviewer**, and the **ship moment**.
- **What we deliberately don't build:** no in-browser IDE, no hosting, no video platform, no community, no certificates, no course-authoring UI. Each one is a company on its own; none of them tests the bet.
- **North-star metric:** *Products shipped*, meaning learners who reach "It's live" with a verified public URL.
- **Shape:** about 12 weeks with 1 full-stack/backend engineer, 1 frontend engineer, 1 product designer (part-time) and 1 content author. **Content is the long pole, so it starts in week 1, not week 8.**
- **Backend:** built on this repo (Django + DRF + Postgres + Redis + Celery), after a week-0 cleanup (section 9.1: CI is currently broken and the beat schedule references apps that don't exist).

---

## 1. Problem & opportunity (business analysis)

### 1.1 Problem statements
| # | Who | Pain | Evidence to collect in discovery |
|---|-----|------|----------------------------------|
| P1 | Aspiring builders | Tutorials stop before the hard parts: auth, data, deploy, ops. "Tutorial hell." | 10 interviews; count abandoned side projects |
| P2 | Specialists (FE or BE devs) | Never owned the whole product, and blocked by the layers they don't know | Interviews + survey on "last thing you shipped alone" |
| P3 | Designers / PMs / founders | Can't turn an idea into an MVP without hiring | Interviews; willingness-to-pay test |
| P4 | Everyone | No feedback loop: "Is what I built right? Is it secure? Is it production-ready?" | Search-intent and forum analysis |

### 1.2 Jobs to be done
1. *When I have an idea, I want a clear next step, so I keep moving instead of researching forever.*
2. *When I finish a step, I want proof it works, so I trust my progress.*
3. *When I'm stuck, I want feedback on **my** code in context, so I'm not left with generic answers.*
4. *When it's live, I want to show it, so the effort turns into credibility (portfolio, users, a job).*

### 1.3 Positioning recap
A new category: product-capability learning. The unit of value is **a shipped product**, not a completed course.

### 1.4 Riskiest assumptions (the MVP exists to test these, in order)
| # | Assumption | How the MVP tests it | Kill / pivot signal |
|---|-----------|----------------------|---------------------|
| A1 | People will do multi-week work outside our app if we guide and verify it | Station-to-station retention | <20% of activated users reach Station 4 |
| A2 | Automated verification + AI review gives enough confidence to replace a mentor | "Was this feedback useful?" on every review; time-to-unblock | <60% "useful" after 2 prompt iterations |
| A3 | Shipping is the motivator (the "It's live" moment) | Ship rate; launch-card shares | Learners stall at Deploy despite completing Build |
| A4 | People will pay before they've shipped | Paywall after Station 3 | Paywall conversion far below plan (set the target with the founder) |

> The thresholds above are **proposed** starting targets, not benchmarks. Revise them after cohort 1.

---

## 2. Users & personas (MVP focus)

| Persona | In MVP? | Notes |
|---------|---------|-------|
| **The Ambitious Builder** (primary) | Yes, design for them | Has ideas, has unfinished projects, some coding exposure |
| The Specialist | Supported | Can skip "learn" steps; "check" steps still gate |
| The Maker-Founder | Supported | Brings their own idea instead of a template |
| The Crossover (designer/PM) | Partially | Needs more learn content in stations 5–7; watch the data |
| Absolute beginner (never written code) | **Not targeted** | A prerequisite check tells them honestly and points to a primer. Revisit post-MVP |

**Prerequisites we state up front:** a laptop, about 5 hours a week, a GitHub account (created during onboarding if needed), and having written *some* code before (one tutorial is enough).

---

## 3. MVP scope

### 3.1 MoSCoW
**Must**
- Auth: email magic link + GitHub OAuth
- Onboarding (3 questions + project choice)
- One path, 9 stations, ~45 steps, rendered from a content repo
- Step types: **Learn**, **Build**, **Check**, **Ship**
- Progress model + the Line visual + resume-where-you-left-off
- Project workspace: repo link, live URL, step-derived task list, check history
- Automated verification: GitHub checks + URL checks, run async
- AI reviewer on Build/Check steps, with usage caps
- Ship moment, public project page, launch card (OG image)
- Transactional email: magic link, verification result, nudges
- Product analytics events + an admin dashboard for the funnel

**Should**
- Paywall after Station 3 (Stripe Checkout, one plan, monthly)
- Streaks, timezone-correct, with a 1-day grace
- Dark mode (the brand supports both themes)

**Could**
- Bring-your-own-idea project template generator (AI-assisted spec)
- Weekly "what you shipped" email
- Public "Shipped this week" gallery

**Won't (MVP)**
- In-browser IDE or sandboxes, hosting, video, forums/community, certificates, multiple paths, a content-authoring UI, mobile apps, teams/B2B, i18n beyond string extraction

### 3.2 The path (content outline v0)
Outcome-named: **Ship your first full-stack product.** Three starter projects (Habit Loop, Waitlist SaaS, Link-in-bio), or bring your own idea.

| # | Station | Role taught | Example steps (type) | Gate (check) |
|---|---------|-------------|----------------------|--------------|
| 1 | Idea | Founder | Problem statement (Build), Scope cut to 3 features (Build) | Self-attest + AI review of the one-pager |
| 2 | Product | PM | User stories, success metric, MVP spec | AI review of the spec |
| 3 | UX/UI | Designer | Core flow wireframe, design tokens | Screenshot upload + self-attest |
| 4 | System | Architect | Data model, API contract, ADR #1 | `docs/adr/0001-*.md` exists in repo |
| 5 | Build | Engineer | Scaffold, CRUD API, frontend wiring, auth | Repo has commits; `/health` route in code |
| 6 | Test | QA | Unit tests, one e2e test, CI workflow | GitHub Actions run on default branch = success |
| 7 | Deploy | DevOps | Env vars & secrets, prod DB, deploy | `GET {live_url}/health` → 200 with token |
| 8 | Run | SRE | Error tracking, uptime alert, logs | Health check passes 3× over 24h |
| 9 | Iterate | You, again | Retro, 1 user interview, ship v1.1 | New deploy detected after launch date |

**Content production budget:** about 45 steps × (draft, review, test-run by a real person) ≈ the largest single work item in the plan. See section 10.

---

## 4. Core user flows

### 4.1 First session (target: first "done" step within 15 minutes)
1. **Landing** → "Start your first build"
2. **Sign up** with GitHub (one click, preferred, because we need the repo anyway) or email magic link
3. **Onboarding, 3 screens, one question each, skippable after the first:**
   1. "What do you want to exist that doesn't yet?" (free text, 280 chars; we keep it, and it becomes the project idea)
   2. "How much time per week?" (2–4h / 5–8h / 10h+, sets pacing and nudge cadence)
   3. "Have you deployed anything before?" (No / Once / Often, adjusts hint depth only, **never gates**)
4. **Pick a project:** 3 starter cards plus "My own idea" (pre-filled from Q1)
5. **Dashboard** with Station 1, Step 1 open; the CTA is "Start step 1 · 8 min"
6. **Step 1 (Build):** write a problem statement in an in-app editor → AI review → done → the Line moves. **Activation event.**

### 4.2 Core loop
Dashboard → Continue → Step (read, build in their own tools) → "Check my work" → verification runs (live status) → pass: next step unlocks / fail: an exact explanation of what we checked and how to fix it → back to the dashboard.

### 4.3 Ship flow (Station 7, final step)
1. Learner enters their live URL. We show the exact check we will run *before* running it.
2. We add a one-time token they expose at `/health` (or as a meta tag) to prove ownership.
3. Check passes → **full-screen ship moment** (Heat gradient, "It's live.", URL, deploy summary).
4. CTAs: **Share your launch** (launch card + prefilled post text, which they edit) and **Start Station 8**.
5. A public project page goes live at `/p/{handle}/{project}`. The learner chooses public or unlisted at this moment; the default is unlisted.

### 4.4 Failure flows (designed, not left over)
| Situation | Behaviour |
|-----------|-----------|
| Check fails | Show **what we checked**, **what we got** (status, body excerpt, timing), **likely causes** (ranked), **retry**. Never just "failed." |
| Check times out / our worker is down | "We couldn't run the check. That's on us, not you." Auto-retry with backoff; the step is not marked failed |
| GitHub token revoked | Banner: "Reconnect GitHub to keep checks running." Progress is never lost |
| Content updated mid-path | The learner stays pinned to their path version; new steps appear as optional "What's new" |
| AI review quota reached | Explain the limit and when it resets; self-attest stays available so nobody is hard-blocked |
| Learner stuck > 3 days on a step | Nudge email with the specific step + "Skip for now" (logged; Check gates still apply before Ship) |

---

## 5. UX/UI specification

### 5.1 Information architecture & routes
| Route | Screen | Auth |
|-------|--------|------|
| `/` | Landing | Public |
| `/login`, `/auth/callback` | Auth | Public |
| `/onboarding/[1-3]`, `/onboarding/project` | Onboarding | User |
| `/home` | Dashboard | User |
| `/path` | Path overview (the Line, all stations) | User |
| `/path/[station]/[step]` | Step view | User |
| `/project` | Project workspace (Board · Checks · Notes · Settings) | User |
| `/ship` | Ship moment (only reachable on pass) | User |
| `/p/[handle]/[project]` | Public project page | Public |
| `/settings` | Account, GitHub connection, billing, data export/delete | User |
| `/admin/*` | Django admin (content preview, funnel, users) | Staff |

### 5.2 Key screens: what must be true
**Dashboard.** It answers *one* question: what do I do next? It shows one primary card ("Current build") with the Line, the next step's title plus an **honest** time estimate, and a single Orange CTA. A secondary card shows "Roles you can cover" (progress by role, not percentage of course). There are no feeds, no leaderboards and no badge walls.

**Step view.** It has a two-pane layout on ≥1024px: content on the left (max 72ch), a sticky action rail on the right (checklist, "Check my work", status, AI review). Below that width it becomes a single column with a bottom action bar. Build steps carry a "Best on a laptop" tag. Code blocks get a copy button, filename and language; commands are separated by OS where they differ.

**Check result panel.** It shows a live status (queued → running → passed/failed) over SSE or WebSocket (Channels is already in the stack), with timestamps and duration. On failure it expands to "What we checked / What we got / Try this".

**Ship moment.** Full screen, shown once, and replayable from the project page. It respects `prefers-reduced-motion`.

### 5.3 Design system implementation
- Tokens from Brand Guidelines 1.0 become CSS variables plus a Tailwind theme: color (light/dark), type scale, spacing (8px base), radius (0/4/8/pill), elevation (1px hairline, 6px hard offset shadow).
- Components (MVP set): Button (primary/secondary/ghost/destructive), Input, Textarea, Select, Checkbox, Tabs, Card, Badge/Status pill, Progress Line, Toast, Modal/Sheet, Tooltip, Code block, Markdown renderer, Empty state, Skeleton, Avatar, Nav (sidebar + mobile bottom bar).
- **State matrix required for every interactive component:** default, hover, focus-visible, active, disabled, loading, error, and empty where relevant. Every state is designed, built and in Storybook before a screen uses it.

### 5.4 Small details that matter (the checklist)
**Trust & honesty**
- [ ] Time estimates come from real median completion times after cohort 1; until then they're labelled "about".
- [ ] Every check states exactly what it verifies before it runs.
- [ ] Never claim that a code review is a security audit. AI review copy says "review," not "approval."

**Flow & momentum**
- [ ] "Continue" always resumes the exact step **and scroll position**.
- [ ] Autosave every editor field (debounced 800ms) with a quiet "Saved" indicator; no Save buttons.
- [ ] Optimistic UI on step completion, rolled back with a toast if the server rejects it.
- [ ] Keyboard: `J/K` previous/next step, `⌘/Ctrl+Enter` to "Check my work", `?` for the shortcut sheet.
- [ ] Deep links work everywhere, including a specific check result.

**Feedback & states**
- [ ] Skeletons, not spinners, for page loads; a spinner only inside a pressed button.
- [ ] Every list has a written empty state (copy from the brand voice bank).
- [ ] Every error message has a cause and a next action. No raw stack traces, and no "Something went wrong" without an ID to quote to support.
- [ ] Offline banner; queued actions retry when the connection returns.

**Time & streaks**
- [ ] Streaks are computed in the learner's **local timezone**, with a 1-day grace per week. DST is tested.
- [ ] Relative timestamps ("2 hours ago") with an absolute tooltip.

**Accessibility (WCAG 2.2 AA)**
- [ ] Contrast pairs from the brand book only; never white text on Orange.
- [ ] Status is never conveyed by color alone (icon + word).
- [ ] Focus ring: 2px Orange, 2px offset, never removed.
- [ ] Hit targets ≥ 44×44px on touch.
- [ ] `prefers-reduced-motion` disables the fold animations.
- [ ] Every page has one `h1`, landmarks and a skip link; Markdown content keeps its heading order.

**Content & copy**
- [ ] Voice rules enforced: "builders" not "learners"; no "unlock / empower / journey".
- [ ] All UI strings are extracted for i18n from day one (English only at launch).

**Privacy & control**
- [ ] Projects are unlisted by default; going public is an explicit choice at the ship moment.
- [ ] Export my data (JSON) and Delete my account are self-serve in settings (reuse `apps.privacy`).
- [ ] GitHub scope is the minimum we need (see 6.5), explained in plain words on the consent screen.

---

## 6. Technical architecture (senior engineering)

### 6.1 Overview
```
            ┌──────────────────────┐
 Browser ──▶│ Web app (Next.js)    │──── SSR/RSC, auth cookie (httpOnly)
            └─────────┬────────────┘
                      │ REST (OpenAPI-typed client) + SSE/WebSocket
            ┌─────────▼────────────┐       ┌───────────────┐
            │ API (Django + DRF)   │──────▶│ Postgres      │
            │ this repo            │       └───────────────┘
            └──┬────────┬──────────┘       ┌───────────────┐
               │        └─────────────────▶│ Redis         │ cache, Celery broker, Channels
               │                           └───────────────┘
            ┌──▼─────────────────────┐
            │ Celery workers         │──▶ GitHub API (GitHub App)
            │  • checks (sandboxed)  │──▶ Learner URLs (SSRF-guarded egress)
            │  • AI reviews          │──▶ Claude API
            │  • launch cards        │──▶ Object storage (S3-compatible)
            └────────────────────────┘
 Content repo (Markdown + YAML) ──CI──▶ `manage.py sync_content` ──▶ Postgres
```

### 6.2 Key decisions
| Decision | Choice | Why | Trade-off |
|----------|--------|-----|-----------|
| Backend | **This Django/DRF repo** | Auth, files, notifications, privacy, Celery and Channels already exist | Must clean out the inherited domain apps first (9.1) |
| Frontend | Next.js (App Router) + TypeScript + Tailwind + Radix primitives | SSR for public/SEO pages, mature ecosystem, accessible primitives | Two deployables |
| API contract | drf-spectacular → generated TS client | One source of truth, no hand-written types | Codegen step in CI |
| Auth | GitHub OAuth + email magic link; JWT in an **httpOnly cookie** (simplejwt is already installed) | Fewer passwords; GitHub needed anyway | Must handle email-less GitHub accounts |
| Content | **Content-as-code** repo (Markdown + front-matter), synced by a management command, versioned | Writers use PRs, reviews and diffs; no CMS to build | Non-technical authors need a little git training |
| Verification | Declarative `check_spec` per step, executed by Celery | Add checks without code changes; auditable | Spec DSL has to be designed carefully |
| Realtime | SSE for check status (Channels as fallback) | Simple, one-directional | — |
| AI | Claude API: `claude-sonnet-5-5` for reviews, `claude-haiku-5-5` for hints and triage | Quality where it matters, low cost for high volume | Vendor dependency; prompts versioned in the repo |
| Hosting | Managed containers + managed Postgres + managed Redis | No ops heroics for an MVP | Cost scales with usage |
| Analytics | PostHog (product events) + Sentry (errors) | Funnels, cohorts and session replay out of the box | Session replay must mask editor fields |

### 6.3 New Django apps
```
api/apps/
  learning/       Path, Station, Step, PathVersion, Enrollment, StepProgress
  projects/       Project, ProjectNote, Task (derived from steps)
  verification/   CheckRun, check executors (github, http, ci, file, attest)
  reviews/        Review, prompt templates, usage ledger
  launches/       Launch, launch-card renderer
  billing/        Subscription (Stripe), webhook handler      [Should]
```

### 6.4 Data model (MVP)
| Model | Key fields | Notes |
|-------|-----------|-------|
| `PathVersion` | path, version (semver), content_hash, published_at | Immutable once published |
| `Station` | path_version, order, slug, title, role | |
| `Step` | station, order, slug, type{learn,build,check,ship}, est_minutes, body_md, check_spec (JSON), requires_laptop | `unique(station, slug)` |
| `Enrollment` | user, path_version, started_at, status{active,paused,shipped,abandoned}, pace{2-4,5-8,10+} | One active enrollment per user in the MVP |
| `StepProgress` | enrollment, step, status{locked,available,in_progress,done,skipped}, started_at, completed_at, attempts, last_scroll | `unique(enrollment, step)` |
| `Project` | user, enrollment, name, slug, idea, repo_full_name, repo_id, live_url, visibility{unlisted,public}, ownership_token | `slug` unique per user |
| `CheckRun` | project, step, kind, status{queued,running,passed,failed,error}, request (JSON), result (JSON), duration_ms, attempt | Append-only; this is the deploy log |
| `Review` | project, step, model, prompt_version, input_tokens, output_tokens, verdict{looks_good,changes_suggested}, findings (JSON), helpful (nullable bool) | `helpful` feeds A2 |
| `UsageLedger` | user, period, reviews_used, tokens_used | Enforces caps |
| `Launch` | project, url, shipped_at, card_image (file), shared_at | One per project for the MVP |
| `Subscription` | user, stripe_customer_id, stripe_subscription_id, status, current_period_end | Webhook-driven only |

### 6.5 Verification engine
Example `check_spec` values (YAML in the content repo):
```yaml
# Station 6 · CI is green
kind: github.workflow_status
branch: default
expect: success
max_age_hours: 72

# Station 7 · It's live
kind: http.get
url: "{project.live_url}/health"
expect:
  status: 200
  body_contains: "{project.ownership_token}"
timeout_ms: 5000
```
Executors: `attest`, `ai_review`, `github.file_exists`, `github.commits_since`, `github.workflow_status`, `http.get`, `http.repeat` (Station 8: three passes over 24h).

**Security requirements (non-negotiable):**
- **SSRF guard** on every outbound URL: https/http only; resolve DNS and **block private, loopback, link-local and metadata ranges** (including IPv6 and DNS rebinding: pin the resolved IP); no redirects into private space; 5s timeout; 1 MB body cap; a dedicated egress worker queue.
- **GitHub App** (not OAuth repo scope): read-only *Contents*, *Metadata* and *Actions*, installed on **selected repos only**. Tokens encrypted at rest and never logged.
- Rate limits on "Check my work": per user (e.g. 10/min) and per project; idempotency keys so double-clicks don't double-run.
- Ownership token proves the learner controls the URL before anything is published.

### 6.6 AI reviewer
- **Input:** the step rubric (from the content repo), the learner's submission (text, or a bounded set of repo files: max N files and M KB, chosen by the step's `review_paths`), and project context.
- **Output:** structured JSON (verdict, up to 5 findings each with file/line/why/how-to-fix, and one thing done well), rendered with the brand voice.
- **Guardrails:** repo content is **untrusted input**. It is delimited in the prompt, and the model is instructed to ignore any instructions inside it; output is schema-validated. Never execute learner code. Per-user monthly review cap plus a global daily budget alarm. Prompts are versioned (`prompt_version` is stored on each `Review`).
- **Quality loop:** a 👍/👎 on every review, a weekly sample review by the content author, and a prompt regression set (20 fixtures per step type) run in CI.

### 6.7 API surface (v1, REST)
```
POST   /api/auth/github/callback        POST /api/auth/magic-link        POST /api/auth/logout
GET    /api/me                          PATCH /api/me                    DELETE /api/me
POST   /api/onboarding                  GET  /api/paths/current
GET    /api/enrollment                  GET  /api/enrollment/steps/{slug}
POST   /api/enrollment/steps/{slug}/start         POST /api/enrollment/steps/{slug}/complete
POST   /api/projects                    GET/PATCH /api/projects/{id}
POST   /api/projects/{id}/checks        GET  /api/projects/{id}/checks?step=
GET    /api/checks/{id}/stream   (SSE)
POST   /api/projects/{id}/reviews       PATCH /api/reviews/{id}  (helpful)
POST   /api/projects/{id}/launch        GET  /api/public/projects/{handle}/{slug}
POST   /api/billing/checkout            POST /api/billing/webhook (Stripe, signature-verified)
```
Conventions: cursor pagination, RFC 7807 problem+json errors carrying a `request_id`, `Idempotency-Key` on POSTs that trigger work.

### 6.8 Non-functional requirements
| Area | Target |
|------|--------|
| Performance | p75 LCP < 2.5s on dashboard and step pages; API p95 < 300ms (excluding checks) |
| Check latency | `http.get` result shown < 10s p95; GitHub checks < 20s p95 |
| Availability | 99.5% monthly for the MVP; status page |
| Data | Daily backups with PITR, restore tested once before beta |
| Security | OWASP ASVS L1, dependency scanning, secrets in a vault, CSP headers, cookie `Secure; HttpOnly; SameSite=Lax` |
| Privacy | GDPR basics: DPA with vendors, data export/delete, analytics consent banner in the EU |
| Observability | Sentry (FE+BE), structured JSON logs with `request_id`, Celery queue-depth alerts, an AI-spend dashboard |

### 6.9 Testing strategy
- **Backend:** pytest + pytest-django (already configured). Unit tests for every check executor, with mocked GitHub and HTTP; SSRF test suite (private IPs, rebinding, redirects).
- **Frontend:** component tests + Storybook for the state matrix; axe accessibility checks in CI.
- **End-to-end (Playwright):** the golden path *sign up → onboarding → complete step 1 → run a passing HTTP check → ship screen*, plus 3 failure paths.
- **Content tests:** a lint for every step (front-matter schema, links, a valid `check_spec`, est_minutes set) runs on every content PR.
- **AI eval set:** run on every prompt change; block the merge on regressions.

---

## 7. Analytics & success metrics

**North star:** verified products shipped per week.

**Funnel events** (name · trigger):
`landing_viewed` → `signup_completed` → `onboarding_completed` → `project_created` → `step_completed{station,step}` → **`activated`** (first Build step done within 24h of signup) → `station_completed{n}` → `paywall_viewed` → `subscription_started` → `check_passed{kind}` → **`shipped`** → `launch_shared`.

| Metric | Definition | Proposed MVP target* |
|--------|------------|----------------------|
| Activation | % of signups with `activated` within 24h | ≥ 40% |
| Station-4 reach | % of activated users reaching Station 4 within 14 days | ≥ 35% |
| Ship rate | % of activated users who ship within 45 days | ≥ 15% |
| Review usefulness | % of 👍 among rated reviews | ≥ 70% |
| Paywall conversion | % of users who view the paywall and subscribe | Set with the founder |
| Time to unblock | Median time from a failed check to a passed check | Track; aim to reduce |

\*Targets are hypotheses to set expectations, not industry figures. Re-baseline after cohort 1.

**Qualitative:** a 15-minute interview with every 5th shipper and every 5th person who abandons at the same station.

---

## 8. Business model (MVP experiment)
- **Free:** Stations 1–3 (idea, product, UX), enough to commit to a project and feel the method.
- **Paid:** a single monthly plan unlocks Stations 4–9 and raises the AI review cap. Price: **[€__ / month, to set with the founder]**; test two price points across cohorts, not within one.
- **No annual plan, coupons or teams in the MVP.** One Stripe product, Checkout plus webhooks, no custom billing UI beyond "Manage subscription" (the Stripe portal).
- **Unit-economics guardrail:** AI spend per paying user per month stays below **[__% of price]**, enforced by the usage ledger plus a budget alarm.

---

## 9. Delivery plan

### 9.1 Week 0: foundations in this repo (do first)
These are issues found while reviewing the repo. Checked items are done (see the "Week 0 progress" note below).
- [x] **CI is broken:** `.github/workflows/ci.yml` runs `cd noev-backend`, but the repo root *is* the project. Fix the paths and add a pytest job.
- [x] **Celery beat references missing apps:** `api/config/settings/components/cron.py` schedules tasks in `apps.stats`, `apps.video_ai`, `apps.payment`, `apps.stats_ext`, and points at a scheduler class that doesn't exist. Remove them so beat can start. *(Logger entries for `apps.cards` / `apps.payment` remain; harmless, clean up with the inherited apps.)*
- [ ] **Inherited domain apps** (`company`, `competitor`, `funding`, `revenue`, `stakeholder`, `accounts.founder`) belong to another product. Decision needed: remove them (recommended), or disable their URLs and keep them out of the OpenAPI schema.
- [ ] **Version drift:** README says Django 5, `requirements.txt` pins `django<5.0`. Pick one (recommend Django 5.x LTS-track) and pin Python.
- [x] **Repo hygiene:** `README copy.md`, `*.bak` scripts and a committed `api/celerybeat-schedule` file should be removed and ignored.
- [ ] Add `.env.example` documenting every variable the settings read.
- [ ] Add `ruff` + `mypy` (or pyright) + pre-commit; set up Sentry; add a `/health` check covering DB, Redis and Celery.
- [ ] Frontend repo scaffold with the token package from the brand book, plus Storybook.

**Week 0 progress (done):**
- CI now runs the new apps' tests on Python 3.11 and builds the backend image (`docker/backend/Dockerfile`, production target; the image build was not run locally because no Docker daemon was available).
- Beat schedule keeps only the 5 `core.tasks.cache_maintenance` tasks that exist; scheduler points at `django_celery_beat`. A test now fails if the schedule references missing code.
- Removed `README copy.md`, `*.bak` files and the tracked `api/celerybeat-schedule`; `pytest.ini` puts `api/` on the path; tests set `DEBUG=0`.
- Started M1–M3 backend: `learning` (content-as-code paths, enrollment, linear progress), `projects`, `verification` (`attest` and SSRF-guarded `http.get` checks, async via Celery, idempotency keys, rate limit). 99 tests.

**Still open:** the inherited suite (about 400 failing or erroring tests in auth, files, notifications, countries and others) predates this work. Fix it or remove those apps (decision 2 in section 11). The `.env.example`, ruff/mypy and Sentry items are not done yet.

### 9.2 Milestones (2-week sprints)
| Wk | Milestone | Engineering | Design | Content | Exit criteria |
|----|-----------|-------------|--------|---------|---------------|
| 0–1 | **M0 Foundations** | Week-0 list; CI/CD to staging; FE scaffold; tokens | Final tokens, component state matrix | Path outline, step template, voice guide | Deploy-on-merge to staging works |
| 2–3 | **M1 Learn** | Auth (GitHub + magic link), `learning` app, content sync, step renderer, onboarding | Onboarding, step view, dashboard (hi-fi) | Stations 1–3 written | A user can sign up and complete step 1 |
| 4–5 | **M2 Progress** | StepProgress, the Line, resume, projects app, autosave notes, analytics events | Project workspace, empty/error states | Stations 4–5 written | Funnel visible in PostHog |
| 6–7 | **M3 Verify** | GitHub App, check engine + SSRF guard, SSE status, AI reviewer + caps, eval set | Check result panel, review UI | Stations 6–7 + check specs | All Station 1–7 gates run automatically |
| 8–9 | **M4 Ship** | Ship flow, ownership token, launch card renderer, public page, Stripe paywall, emails | Ship moment, launch card, public page | Stations 8–9; email copy | End-to-end golden path passes in Playwright |
| 10 | **M5 Harden** | Load test checks, security review, a11y audit, backups/restore drill, rate limits | Polish pass against the details checklist | Full test-run of the path by 3 outsiders | Zero P0/P1 bugs; a11y AA pass |
| 11–12 | **M6 Beta → Launch** | Closed beta (30–50 builders), fix loop, launch | Iterate on data | Fix where people stall | Ship-rate and usefulness readouts |

### 9.3 Team & RACI (lean)
| Area | Responsible | Accountable | Consulted |
|------|-------------|-------------|-----------|
| Product scope & metrics | PM/Founder | Founder | All |
| Backend, verification, AI | BE engineer | Tech lead | Security reviewer |
| Frontend & design system | FE engineer | Tech lead | Designer |
| UX/UI | Designer | Founder | FE |
| Path content & rubrics | Content author | Founder | BE (check specs) |

### 9.4 Definition of Done (per story)
Acceptance criteria met · tests (unit + e2e where relevant) · every state in the state matrix built · a11y check passes · analytics event wired · copy reviewed against the voice guide · feature-flagged if risky · deployed to staging · docs/ADR updated if architecture changed.

---

## 10. Risks & mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Content takes longer than engineering** | High | High | Start in week 1; a step template; test each station with real people as it lands; launch with 9 stations even if some are thin |
| Learners stall at Deploy (the hardest station) | High | High | Two supported hosting targets with exact guides; a pre-flight checklist; the AI reviewer reads their error log |
| SSRF or abuse through URL checks | Medium | Critical | Guard in 6.5, isolated egress queue, pen-test before beta |
| AI cost overrun | Medium | Medium | Caps per user, global budget alarm, Haiku for triage, cache identical reviews |
| AI gives wrong or overconfident feedback | Medium | High | Rubric-bound prompts, eval set, "review not approval" copy, 👎 feedback loop |
| GitHub API rate limits | Low | Medium | GitHub App installation tokens (higher limits), webhooks over polling, backoff |
| Scope creep (IDE, community, more paths) | High | High | The Won't list is signed off by the founder; new ideas go to a post-MVP backlog |
| Name not cleared | Medium | Medium | Trademark search before public launch; the brand system is name-independent |

---

## 11. Open decisions for the founder
1. **Price point and paywall position** (after Station 3 is recommended).
2. **Remove the inherited domain apps from this repo?** (recommended: yes)
3. **Which two hosting providers** do the Deploy guides support?
4. **Starter projects:** confirm the 3 (Habit Loop, Waitlist SaaS, Link-in-bio).
5. **Beta cohort source:** waitlist, a community partner or paid acquisition?
6. **Data residency:** EU-hosted from day one?
7. **Name clearance** for "Onefold" or an alternative before the public launch.

---

## 12. Post-MVP (only if the bets in 1.4 pass)
More paths ("Ship a paid SaaS", "Ship an AI product", "Ship a mobile app") · bring-your-own-idea spec generator · mentor office hours (paid) · a public gallery of shipped products · teams/B2B for bootcamp replacement · in-browser preview sandboxes.
