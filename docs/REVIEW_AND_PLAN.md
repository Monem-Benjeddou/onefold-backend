# Onefold — State review & plan to a real MVP

> Senior engineering + UX review of `main` at `f0bb00c`, measured against `MVP_PLAN.md`.
> Date: 2026-10-08 · Rev 2: sign-in, local inbox and onboarding added as Phase 0 (top priority).

---

## 1. Verdict

The **plumbing is solid; the product is hollow.** Auth, the progress engine, the SSRF-safe
check runner, the BFF cookie setup and the seeder are production-grade. What a builder actually
*experiences* is not:

| Measure | Plan | Today |
|---|---|---|
| Steps in the path | ~45 | **10** |
| Words of teaching content (whole path) | a course | **584** (≈ one blog post) |
| Steps with a real automated check | most gates | **1** (`http.get` on Deploy); the other 6 are a checkbox ("attest") |
| GitHub sign-in / repo + CI checks | Must | none |
| AI reviewer | Must | none |
| Screens from the IA (§5.1) | 11 | 8 (no Settings, no public project page, no onboarding project picker) |
| UI states (loading / error / empty) | every screen | **no `loading.tsx` or `error.tsx` anywhere** |

So it *feels* broken even where nothing throws: you click through ten thin pages, tick boxes,
and you're "done". That's the core problem, and it's mostly **content + verification**, not code
quality. The fixes below are ordered by how much each one changes that feeling.

**But the very first thing a person touches is broken too: getting in.**
- Signing in locally means digging a link out of `docker compose logs`.
- The login page is one email field, with no password, no sign-up, no SSO and no recovery.
- Onboarding loses your answers and can leave you stuck.

That's why it's **Phase 0**, ahead of everything else.

---

## 2. What's wrong, by severity

### P0-A — Getting in (top priority, fix first)
1. **Local sign-in needs container logs.**
   - The email backend is the console, so the magic link only exists in `docker compose logs api`.
   - Nobody should have to read logs to use the app. That's a dev-experience failure, not an
     "advanced" workflow.
2. **Authentication is too thin for a real product.**
   - Magic link is the *only* way in: no password option, no "Continue with Google/GitHub", no
     separate sign-up, and no account recovery story.
   - People expect email + password, and corporate email scanners and slow inboxes make
     link-only sign-in fragile.
3. **The login page isn't product grade.**
   - It's a single card with one field.
   - Missing:
     - The field set: password, show/hide and a caps-lock warning.
     - The flows: "Forgot password?", a switch to sign-up, and SSO buttons.
     - The standards: proper `autocomplete` hints, per-field errors, and a brand panel.
   - Nothing tells you what happens after you submit.
4. **Session expiry breaks things in the middle of a task.**
   - The access cookie lives 60 min (`web/src/lib/session.ts`) but the JWT only 30 min
     (`JWT_ACCESS_MINUTES`). From minute 30 to 60, every request carries a dead token.
   - In the browser, `lib/client.ts` responds to a 401 by **hard-redirecting to /login** without
     trying a refresh. Anything typed is lost: onboarding answers, project settings.
5. **Onboarding loses state and can strand you.**
   - Answers live only in React memory. A refresh, a back button or an expired session wipes them.
   - `finish()` makes two separate calls (create enrollment, then create project).
     - If the second fails, the enrollment already exists, so `/onboarding` redirects you to
       `/home`, and you're in the app with no project and no way back to onboarding.
     - Retrying can hit "already enrolled".
   - The flow contradicts itself:
     - Q1 says "No quiz about your experience", but the plan has an experience question.
     - The progress bar says "3 questions", but the third is a project name.
     - Q1 can be skipped, but the name can't.
   - No way out of it: the logo isn't a link and there's no sign-out on the onboarding page.
   - Missing pieces: Q3 (experience) and the starter-project picker.

### P0-B — makes the product feel fake or broken
1. **Content is a stub.** 10 steps × ~58 words. Steps say *what* to do, never *how*: no commands,
   no code, no screenshots, no "done looks like this". This is the single biggest problem.
2. **Checks are mostly honor-system.** Stations 4–6 (System, Build, Test) are `attest`, so the
   "we check the work" promise on the landing page is false for 6 of 7 gates.
3. **No loading or error states.** Every app page is a Server Component that awaits 2–4 API calls.
   - While they run, navigation shows nothing.
   - On any 5xx, `lib/api.ts` throws, and the builder gets Next's default error screen.
   - Together with the `npm ci` on every web container start, this is the "empty page" you saw.
4. **The step page is a dead end on mobile.** The action rail renders *after* the content in one
   column, so you have to scroll to the bottom to find "Check my work".
   - There's no previous/next step navigation.
   - The tab title is the slug ("go-live").
5. **"You can read ahead" is a lie.** The step page says it, but `/path` renders locked steps as
   non-links, so there's no way to read ahead.

### P1 — missing MVP surface
6. **No Settings:**
   - Can't change name or email.
   - Can't export data.
   - Delete account exists in the API but not in the UI.
   - Sign-out is the only account control.
7. **No public project page** (`/p/[handle]/[project]`) and no launch card.
   - The ship moment has nothing to share.
   - "Unlisted by default; public is a choice at ship" isn't implemented anywhere.
8. *(Onboarding gaps moved to P0-A #5.)*
9. **No in-app writing for Build steps.** Step 1 (problem statement) is supposed to be written in
   Onefold and reviewed; today you write it elsewhere and tick a box.
10. **No skip or "stuck" flow.** Plan §4.4 requires "Skip for now" (logged) and a stuck nudge.

### P2 — engineering debt that will slow everything down
11. **Hand-written API types** (`web/src/lib/types.ts`) drift from the backend. They should be
    generated from drf-spectacular, which is already installed.
12. **Chatty pages.**
    - The app layout fetches `/auth/me/` and `/home` fetches it again, plus three other calls.
    - Every page re-derives "the project" as `projects.results[0]`.
    - One `GET /api/v1/workspace/` aggregate (me + enrollment + project) would remove most of that.
13. **No component kit.** Inputs, textareas, toasts, skeletons and dialogs are re-styled inline in
    each form, so states drift between screens (focus, error, disabled).
14. **Polling at 1s × 45** for check status. Fine for now; back off to 1s→2s→4s and move to SSE later.
15. **Dev loop.** The web container runs `npm ci` on every `up`, and the compose file has no web
    healthcheck. This causes the 30-second blank page. Fixed in Phase 0.1.
16. **No end-to-end test of the golden path.** CI checks types and builds but never signs in.
17. **Not started:** observability (Sentry), analytics events (PostHog), a transactional email
    provider and a deploy target.

### P3 — polish (from the §5.4 checklist)
- Check history:
  - Shows the slug as the step name ("go live") and raw UTC timestamps.
  - Should show the real title and relative time, with the absolute time in a tooltip.
- There's no skip link, and the mobile nav is a cramped top bar (the plan says bottom bar).
- No dark mode, even though the brand defines both themes.
- Code blocks have no copy button.
- Time estimates aren't labelled "about" consistently.
- The landing page has no FAQ, pricing hint or "what you'll need", so the prerequisites aren't
  stated up front.

---

## 3. Target MVP structure

### 3.1 Screens (information architecture)
```
Public
  /                      Landing (hero · how it works · the 9 stations · what you need · FAQ)
  /login                 Email + password · GitHub/Google · magic link   REBUILD (Phase 0)
  /signup                Create account                                  NEW (Phase 0)
  /forgot-password       Request reset                                   NEW (Phase 0)
  /reset-password        Set new password                                NEW (Phase 0)
  /verify-email          Confirm email (POST, scanner-safe)              NEW (Phase 0)
  /auth/verify           Confirm magic-link sign-in (POST, scanner-safe) ✓ exists
  /p/[handle]/[project]  Public project page + OG launch card            NEW

Builder
  /onboarding?step=1-4   Idea → Pace → Experience → Pick project, saved REBUILD (Phase 0)
  /home                  Next step · the Line · roles covered · recent checks
  /path                  All stations; locked steps readable (read-ahead)
  /steps/[slug]          Content · sticky action rail (desktop) / bottom bar (mobile)
                         · prev/next · in-app editor on Build steps · AI review panel
  /project               Tabs: Overview · Checks · Settings (repo, URL, token, visibility)
  /ship                  Ship moment → choose public/unlisted → share card   EXTEND
  /settings              Profile · Password · Signed-in devices · Connected accounts
                         · Export data · Delete account                  NEW

Staff
  /admin                 Django admin (+ funnel view later)              ✓ exists
```

### 3.2 Backend modules
| App | Has | Adds |
|---|---|---|
| `accounts` | magic link, JWT, `/me` | password sign-up/login, reset, email verification, GitHub + Google SSO, throttling, sign-in audit, device sessions, handle, `/me/export` (Phase 0) |
| `onboarding` (in `learning`) | — | `POST /onboarding/` (atomic, idempotent), saved draft, `onboarding_complete` on `/me` (Phase 0) |
| `learning` | paths, progress, sync | `skip`, submissions (in-app text per step), `/workspace` aggregate |
| `projects` | project, token | starter templates, public read endpoint |
| `verification` | `attest`, `http.get` | `github.file_exists`, `github.workflow_status`, `github.commits_since`, `http.repeat` |
| `reviews` | — | AI review (Claude), usage cap, 👍/👎 |
| `launches` | — | launch record, OG card render |

### 3.3 Content (the real long pole)
45 steps across 9 stations, each following one template:

> **Why** (2–3 lines) → **Do this** (numbered, with commands/code per OS) →
> **Done looks like** (a screenshot or snippet) → **Check** (what we verify, stated before it runs) →
> **If it fails** (the 3 most common causes).

Gates move off `attest` wherever a machine can decide:

| Station | Gate |
|---|---|
| Idea / Product | in-app text + AI review |
| UX/UI | screenshot upload + attest |
| System | `docs/adr/0001-*.md` exists in the repo |
| Build | `/health` route committed |
| Test | CI green on the default branch |
| Deploy | `GET /health` → 200 + token ✓ |
| Run | 3 passes over 24h |
| Iterate | new deploy after the launch date |

---

## 4. Phased plan

Each phase ends in something you can click through. Order is by impact on "does this feel real".

### Ground rules (apply to every phase)
- **Nothing requires reading logs or running commands to use the app.** Every link, email or
  token a person needs is reachable from a browser, locally and in production.
- **A refresh, back button or expired session never loses what someone typed.**
- **Every flow is one transaction.** No half-finished accounts, enrollments or projects.
- **Every screen has a designed loading, empty and error state before it ships.**

### Phase 0 — Sign-in and onboarding, product grade (≈ 1 week, TOP PRIORITY)

**0.1 Local developer experience: no more logs**
- Add **Mailpit** to `docker-compose.yml`.
  - Every email (magic links, password resets, verification) lands in a web inbox at
    `http://localhost:8025`.
  - Wire it with `EMAIL_BACKEND=smtp`, `EMAIL_HOST=mailpit`, `EMAIL_PORT=1025`.
- In development only, the "check your inbox" screen shows an **Open local inbox →** button.
- **Seeded demo accounts get a password** (`onefold`, from `SEED_DEMO_PASSWORD`) so you sign in
  with the form directly.
- **Dev-only "Sign in as…" panel** on the login page lists the demo accounts.
  - It shows new, ada, grace, linus and admin; one click each.
  - It's rendered only when the API reports `DEBUG` *and* `NEXT_PUBLIC_DEMO_LOGIN=1`.
  - The API endpoint behind it returns 404 unless `DEBUG` is on.
- Install web dependencies in the image, not on every start, and add a web healthcheck.
  `docker compose up` then reaches a working page in seconds, not after a 30-second blank screen.
- On startup the API prints one box with every URL: app, inbox, admin, API docs and demo logins.

**0.2 Authentication, enterprise level (backend)**

| Capability | Endpoint / detail |
|---|---|
| Sign up with email + password | `POST /auth/register/` with name, email, password. Django password validators (min 10 chars, not common, not similar to the email). Sends a verification email; the person can use the app right away and sees a banner until they verify. |
| Sign in with password | `POST /auth/login/` → JWT pair. Generic error ("Email or password is wrong"); never reveals whether an account exists. |
| Magic link (kept) | Existing endpoints. Becomes "Email me a sign-in link instead". |
| Forgot / reset password | `POST /auth/password/forgot/` (always 202) and `POST /auth/password/reset/`. Single-use, hashed token, 30-min TTL. Resetting revokes all refresh tokens. |
| Email verification | `POST /auth/email/verify/`, plus resend with a cooldown. |
| SSO | "Continue with GitHub" now (also needed for checks later), "Continue with Google" next. Accounts link by verified email. |
| Brute-force protection | Throttles per IP and per email (e.g. 5 failures per 15 min, then a cooldown with a clear message). Constant-time responses. |
| Sessions | "Signed-in devices" list with revoke one / revoke all (backed by simplejwt outstanding tokens). |
| Audit | Sign-in, failure, reset and password-change events stored with IP and user agent; visible in admin. |
| Later (Should) | TOTP two-factor and passkeys. |

**0.3 Session handling (web)**
- Align the cookie lifetime with the JWT lifetime (access 30 min, refresh 30 days).
- On a 401, `lib/client.ts` calls a `POST /api/auth/refresh` route and **retries the request once**.
  It goes to `/login?next=…` only if the refresh fails, and keeps the page's draft (see 0.5).
- A middleware refreshes an expiring access token before Server Components render, so pages
  never bounce through redirects.
- "Remember this device": if unticked, the refresh cookie is a session cookie, gone when the
  browser closes.

**0.4 Auth screens (web)**

Layout: split screen. A Carbon brand panel on the left (the Fold, one line of copy, the 9
stations); the form on Paper on the right. On mobile it's a single column with a slim brand header.

| Route | Screen |
|---|---|
| `/login` | Email, password (show/hide, caps-lock warning), "Remember this device", **Sign in**. "Forgot password?" sits next to the password label. A divider, then GitHub and Google, then "Email me a sign-in link instead". A footer link to "Create an account". |
| `/signup` | Name, email, password with a live strength meter and the rules listed (each turns green as it's met), terms consent line, **Create account**, SSO buttons, a "Sign in" link. |
| `/forgot-password` | Email → a confirmation screen that says the same thing either way, with a resend countdown. |
| `/reset-password?token=` | New password + confirm, strength meter → signs you in and goes to `next`. Expired or used tokens get a clear screen with "Send a new link". |
| `/verify-email?token=` | One-click confirm (POST, scanner-safe like magic links). |
| `/auth/verify` | The existing magic-link confirm, restyled to match. |

Details every auth screen must get right:
- **Autofill and password managers:** `autocomplete` set to `email`, `current-password` or
  `new-password`; real `<form>` posts so password managers save credentials.
- **Errors:** validate on submit, never by disabling the button. Show per-field errors linked by
  `aria-describedby`, plus a summary at the top that receives focus. The server error text is
  mapped to human copy.
- **Keeping input:**
  - The email carries over between login, sign-up, forgot-password and magic-link
    (in the query string, never the password).
  - `next` is preserved through every hop, including SSO and email links.
- **Feedback:** loading state inside the pressed button only; a throttled state says exactly
  when to try again.
- **Hygiene:**
  - The page title reflects the screen.
  - It works with JavaScript off for the basic form post.
  - Lighthouse accessibility ≥ 95.
- **Signed-in redirect:** a signed-in person visiting `/login` or `/signup` goes straight to
  `/home` (or `/onboarding`).

**0.5 Onboarding, rebuilt**
- **One backend endpoint, one transaction:** `POST /onboarding/` with idea, pace, experience and
  project choice. It creates the enrollment and the project atomically and is idempotent (calling
  it twice returns the same result).
- **The routing rule moves to the API** as `GET /me` → `onboarding_complete`. Every app page and
  the post-sign-in redirect use it. Someone with an enrollment but no project goes back to
  onboarding instead of being stranded on `/home`.
- **Steps** (URL-addressable, so back/forward and refresh work: `/onboarding?step=2`):
  1. *What do you want to exist that doesn't yet?* Optional, 280 chars.
  2. *How much time per week?* 2–4h, 5–8h or 10h+.
  3. *Have you deployed anything before?* No, once, or often. It only adjusts hint depth and
     never gates.
  4. *Pick your project.* Three starter cards (Habit Loop, Waitlist SaaS, Link-in-bio) plus
     "My own idea", pre-filled from step 1 and editable. The name is pre-filled and editable.
- **Answers are saved as you go:**
  - A per-user draft is saved to the API, so it survives a refresh, a sign-out, another device or
    a session expiry.
  - The draft is restored on return, with a "Welcome back, you were on step 3" line.
- **Copy and controls:**
  - Accurate progress ("Step 2 of 4").
  - Back is always available.
  - The logo goes home, with a quiet "Sign out" in the corner.
  - Remove the contradictory "No quiz about your experience" label.
  - The name question moves to Settings.
- **Finish:**
  - Shows a 1-second "Setting up your build…" state.
  - Lands on `/home` with step 1 highlighted and a one-time "Here's how this works" tip
    (3 bullets, dismissible).
- **Errors:** a failed finish keeps every answer on screen with a retry. It never redirects you away.

**0.6 Tests for Phase 0**
- **Backend:** register, login, throttle and lockout, reset (including token reuse and expiry),
  verify email, the onboarding endpoint's idempotency and atomicity, and the `onboarding_complete`
  routing rule.
- **Playwright in CI:**
  - Sign up → onboarding (including a refresh mid-way) → home.
  - Log in with a seeded account.
  - Forgot password → read the email from the Mailpit API → reset → signed in.
  - An expired access token mid-form, retried without losing input.

**Exit:**
- A brand-new person goes from landing to their first step with no logs and no help.
- Refreshing at any point of onboarding loses nothing.
- All Phase 0 tests are green in CI.

### Phase 1 — Make what exists feel solid (≈ 3–4 days)
- `loading.tsx` skeletons for home, path, step and project pages.
- `error.tsx` boundaries with a cause, a retry and a request ID; `not-found` for unknown steps.
- `/workspace` aggregate endpoint; the layout and pages read from it (one call, not four).
- Step page:
  - Mobile bottom action bar.
  - Prev/next links and the real title in `<title>`.
  - Code-block copy buttons.
  - Scroll restore after the content renders.
- Locked steps readable from `/path` (read-only, action rail says why).
- Component kit: `Input`, `Textarea`, `Field` (label/hint/error), `Toast`, `Skeleton`, `Dialog`,
  `StatusPill`, each with the full state matrix.
- Check history: real step titles, relative time with an absolute tooltip.
- Skip link, a mobile bottom nav, and one `h1` per page.
- **Exit:** every screen has designed loading, empty and error states; Lighthouse a11y ≥ 95.

### Phase 2 — Complete the builder journey (≈ 1 week)
- `/settings`:
  - Profile and password change.
  - Signed-in devices and connected accounts (both from Phase 0).
  - Export JSON.
  - Delete account, with typed confirmation.
- In-app editor on Build steps: autosave (800ms debounce, "Saved" indicator) and stored per step.
- "Skip for now", which logs the skip; Check gates still apply before Ship.
- Ship flow: a public/unlisted choice, then `/p/[handle]/[project]` with an OG launch card.
- Extend the Phase 0 Playwright suite: step 1 → passing `http.get` → ship → public page.
- **Exit:** a new person goes from landing to a shared public page without help.

### Phase 3 — Real verification (≈ 1.5 weeks)
- A GitHub App (read-only Contents, Metadata and Actions, on selected repos). GitHub sign-in
  itself ships in Phase 0.
- Executors: `github.file_exists`, `github.workflow_status`, `github.commits_since`, `http.repeat`.
- Move the System, Build, Test, Run and Iterate gates off `attest`.
- **Exit:** 7 of 9 station gates decided by a machine.

### Phase 4 — Content v1 (runs in parallel from Phase 0; the long pole)
- Write the step template and a voice checklist, plus a lint for content PRs (front-matter,
  `check`, `est_minutes`, links).
- 45 steps, one station at a time; each one test-run by someone who isn't the author.
- Two supported hosting targets for Deploy (decision needed: see §5).
- **Exit:** an outsider ships with the path alone.

### Phase 5 — AI review + launch readiness (≈ 1.5 weeks)
- A `reviews` app:
  - Claude review of in-app text and bounded repo files.
  - Schema-validated output.
  - Per-user cap.
  - 👍/👎 feedback.
- Production basics:
  - A real email provider (Postmark or Resend) replacing Mailpit outside local dev, with SPF,
    DKIM and DMARC set up.
  - Sentry on frontend and backend.
  - PostHog funnel events (§7 of the MVP plan).
  - A deploy target with staging.
- Paywall after Station 3 (Stripe Checkout), if the founder confirms the price.
- **Exit:** closed beta with 30–50 builders.

---

## 5. Decisions needed from you
1. **Hosting targets for the Deploy guides.** Recommendation: Render + Fly.io (both have free
   tiers and simple `/health` setups).
2. **Starter projects.** Confirm Habit Loop, Waitlist SaaS and Link-in-bio.
3. **Who writes the content.** If it's me, I'll draft station by station for you to review. This
   is the critical path.
4. **Where production runs** (for Phase 5), and whether data must stay in the EU.
5. **Sign-in methods at launch.** Recommendation: email + password, GitHub, Google, with the
   magic link kept as a fallback. Two-factor and passkeys follow after the beta.

---

## 6. Recommended next move
1. **Phase 0 first:** sign-in, local inbox, session handling and onboarding. This is the front
   door, and nothing else matters if people can't get in cleanly.
2. Then **Phase 1** (loading and error states, the step page, the component kit).
3. In parallel, draft **Stations 1–2 of the content** to the new template, so you can judge the
   teaching quality before the other 35 steps get written.

| Order | Phase | Size | Why now |
|---|---|---|---|
| 1 | 0 · Sign-in + onboarding | ≈ 1 week | The front door is broken |
| 2 | 1 · Solid states + step page | 3–4 days | The app looks broken while loading or on errors |
| 3 | 2 · Complete the journey | ≈ 1 week | Settings, ship, public page |
| 4 | 3 · Real verification | ≈ 1.5 weeks | The "we check your work" promise |
| ∥ | 4 · Content v1 | ongoing | The long pole; starts with Phase 0 |
| 5 | 5 · AI review + launch | ≈ 1.5 weeks | Beta readiness |
