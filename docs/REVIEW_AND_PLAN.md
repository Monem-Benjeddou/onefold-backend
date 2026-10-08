# Onefold — State review & plan to a real MVP

> Senior engineering + UX review of `main` at `f0bb00c`, measured against `MVP_PLAN.md`.
> Date: 2026-10-08.

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

---

## 2. What's wrong, by severity

### P0 — makes the product feel fake or broken
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
8. **Onboarding is incomplete.**
   - Q3 ("deployed before?") is missing.
   - There's no starter-project picker (Habit Loop / Waitlist SaaS / Link-in-bio / own idea).
   - The name is asked as a "question", which the plan doesn't have.
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
    healthcheck. *(You declined changing this earlier. Still listed, since it's the cause of the
    30-second blank page.)*
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
  /login                 Email magic link  +  "Continue with GitHub"
  /auth/verify           Confirm sign-in (POST, scanner-safe)            ✓ exists
  /p/[handle]/[project]  Public project page + OG launch card            NEW

Builder
  /onboarding            1 Idea → 2 Pace → 3 Experience → 4 Pick project NEW steps
  /home                  Next step · the Line · roles covered · recent checks
  /path                  All stations; locked steps readable (read-ahead)
  /steps/[slug]          Content · sticky action rail (desktop) / bottom bar (mobile)
                         · prev/next · in-app editor on Build steps · AI review panel
  /project               Tabs: Overview · Checks · Settings (repo, URL, token, visibility)
  /ship                  Ship moment → choose public/unlisted → share card   EXTEND
  /settings              Profile · GitHub connection · Export data · Delete account  NEW

Staff
  /admin                 Django admin (+ funnel view later)              ✓ exists
```

### 3.2 Backend modules
| App | Has | Adds |
|---|---|---|
| `accounts` | magic link, JWT, `/me` | GitHub OAuth, handle, `/me/export` |
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
- Onboarding:
  - Add Q3 (experience).
  - Add the starter-project picker (3 cards + "My own idea", pre-filled from Q1).
  - Name moves to Settings.
- `/settings`: profile, export JSON, delete account (with typed confirmation).
- In-app editor on Build steps: autosave (800ms debounce, "Saved" indicator) and stored per step.
- "Skip for now", which logs the skip; Check gates still apply before Ship.
- Ship flow: a public/unlisted choice, then `/p/[handle]/[project]` with an OG launch card.
- Playwright golden path in CI, covering sign in → onboarding → step 1 → passing `http.get` → ship.
- **Exit:** a new person goes from landing to a shared public page without help.

### Phase 3 — Real verification (≈ 1.5 weeks)
- GitHub sign-in, plus a GitHub App (read-only Contents, Metadata and Actions, on selected repos).
- Executors: `github.file_exists`, `github.workflow_status`, `github.commits_since`, `http.repeat`.
- Move the System, Build, Test, Run and Iterate gates off `attest`.
- **Exit:** 7 of 9 station gates decided by a machine.

### Phase 4 — Content v1 (runs in parallel from Phase 1; the long pole)
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
  - Email provider for magic links and check results.
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

---

## 6. Recommended next move
Start **Phase 1** now (small, all code, fixes the "it's broken" feeling). In the same stretch,
draft **Stations 1–2 of the content** to the new template, so you can judge the teaching quality
before the other 35 steps get written.
