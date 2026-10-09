# Onefold — UX plan: "I don't know how to use this" and "I can't find my way around"

> Status: plan, not built. Date: 2026-10-09. Scope: the signed-in app (home, path, step, project, ship).
> Sign-in and onboarding screens are in good shape and change only where noted.

---

## 1. The diagnosis

Two different problems, with different fixes:

**A. Comprehension: people don't understand what Onefold *is for* or what to *do*.**
The app assumes the builder already knows the model: stations, steps, checks, "the Line", a verification token, roles. Nothing teaches it. Work happens **outside** the app (their editor, GitHub, hosting), and the app never says so where it matters.

**B. Navigation: people can't tell where they are or how to get somewhere.**
There are only three tabs. The step page, where people spend most of their time, has no map of where it sits. The way back to "what do I do now" isn't obvious.

### 1.1 What's wrong, screen by screen (from the current build)

| # | Where | What a new builder experiences | Why |
|---|-------|--------------------------------|-----|
| 1 | Everywhere | "Station 07 · Deploy · Ship · About 90 min · Role: DevOps": a line of insider words | Jargon with no definitions (*station, step, check, ship, attest, the Line, roles*) |
| 2 | Everywhere | The status word for the same thing changes per screen | "Up next" (pill), "Next" / "Now" (old path), "Learning" / "Covered" / "Ahead" (home roles), "Start" / "Continue" (buttons) |
| 3 | Home | A striped bar with no labels, and a "Roles you can cover" list that does nothing when clicked | The Line has no legend or hover; the roles aren't links |
| 4 | Home, first visit | Three bullet points, then a card | No "here's how a step works" walkthrough. No "what you'll need" (GitHub account, editor, hosting) |
| 5 | Step page | ~60 words, then a button "I confirm, check it" | Steps don't say what *done* looks like. "Confirm" vs "check" is unclear: is Onefold checking, or me? |
| 6 | Step page | Pressing a check on Deploy sends you to the Project page to add a URL, and you lose your place | Requirements aren't collected *in* the step |
| 7 | Step page | You can't see the other steps in this station, or how far through the path you are | No local map. The previous/next links sit at the very bottom of the content |
| 8 | Step page, locked | You can open a locked step, but it's unclear why you can't do it or how to unlock it | "Reading ahead" is shown, but not "finish *X* first", with a link |
| 9 | Step page, after passing | A toast appears and the page refreshes; the next step is only a button in the side rail | Success isn't a moment, and "what's next" isn't put in front of you |
| 10 | Path | One long flat list of every step | Stations aren't grouped by state, can't be collapsed, and have no per-station progress |
| 11 | Project | A settings form plus a "verification token" box with Express code, from day one | Shown long before it's needed (Station 7), with no explanation of why |
| 12 | Phone | Two fixed bars at the bottom (the step action bar plus the tabs), so less than half the screen is content | Both are fixed and stacked |
| 13 | Ship screen | It sits outside the app shell: no navigation, no way back except its buttons | It's a full-screen page with no shell |
| 14 | Anywhere | Stuck? There's nowhere to go | No help, no FAQ, no glossary, no contact |

---

## 2. Principles for the fix

1. **One obvious next action, everywhere.** From any screen, one tap gets you to "the thing to do now".
2. **Always show "you are here".** Path → station → step, with your progress, visible on every app screen.
3. **Teach in context, not in a manual.** Explain a word the first time it appears, right where it appears.
4. **Say where the work happens.** When a step needs your editor, terminal, GitHub or host, the step says so up front ("You'll work in: Terminal · GitHub").
5. **Ask for what a step needs inside the step.** Never send someone to another page to fill in a field.
6. **One vocabulary.** Every status, verb and noun means the same thing everywhere (§5).
7. **Success and failure are moments**, each with a clear next step.

---

## 3. Navigation model (the new information architecture)

### 3.1 Global shell

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ◧ onefold   Ship your first product   ▓▓▓▓▓▓░░░ 6/10      [ Continue: Deploy → ]  (?)  (A) │
├─────────────┬────────────────────────────────────────────────────────────────┤
│ Today       │                                                                │
│ Path        │                       page content                             │
│ Project     │                                                                │
│ ─────────   │                                                                │
│ Help        │                                                                │
│ Settings    │                                                                │
└─────────────┴────────────────────────────────────────────────────────────────┘
```

- **A top bar on every app screen**, in this order:
  - Path name.
  - **Progress with labels** (6/10 steps, hover/tap → per-station breakdown).
  - **A persistent `Continue: <next step>` button**, the one orange action of the shell.
  - Help (?), and the account menu.
- **Navigation renamed for what people want to do:**
  - **Today** (was Home): what to do now.
  - **Path**: the map.
  - **Project**: your product.
  - **Help**: guides, glossary, contact.
  - **Settings**: account.
- **Phone:**
  - The bottom tab bar holds Today · Path · Project · Help.
  - The step's primary action **replaces the Continue button in the top bar** while you're on a step. One fixed bar, not two (fixes #12).
- **Ship moment** opens inside the shell as a full-width celebration panel, with navigation still present (fixes #13).

### 3.2 "You are here" on the step page

```
Path / 07 Deploy / Put it on the internet                  Step 8 of 10 · Station 7 of 9
┌──────────────────────┬──────────────────────────────────────────┬──────────────────────┐
│ 07 DEPLOY  ▓▓░ 1/2   │  Put it on the internet                  │  WHAT WE CHECK       │
│ ✓ Env vars & secrets │  You'll work in: Terminal · Your host    │  GET <url>/health    │
│ ● Put it on the …    │  ~90 min · Best on a laptop              │  → 200 + your token  │
│                      │                                          │                      │
│ ── Other stations ── │  1 Goal  2 You'll need  3 Do this        │  Your live URL       │
│ ✓ 01 Idea            │  4 Done looks like  5 If it fails        │  [https://…      ]   │
│ ✓ 02 Product         │                                          │  Your token  [Copy]  │
│ …                    │  …content…                               │                      │
│ ○ 08 Run (locked)    │                                          │  [ Check it's live ] │
└──────────────────────┴──────────────────────────────────────────┴──────────────────────┘
```

- **Left: the station outline.**
  - The steps in this station with their status, plus a collapsed list of the other stations.
  - On phones it becomes a "Station 7 · Step 1 of 2 ▾" dropdown under the title (fixes #7).
- **Top: breadcrumb plus "Step 8 of 10".**
- **Previous/Next sits in the step header and at the end of the content**, with J/K shortcuts.
- **Right: the action panel.**
  - It **collects what the check needs right there**: live URL, repo, token with copy.
  - The project form fields are inline, saved without leaving the page (fixes #6).

### 3.3 The Path page as a map, not a list

- **Stations as cards** in a 3×3 grid on desktop and a vertical stack on phones. Each card shows:
  - its role;
  - its progress (`1/2`);
  - its state: **Done / You're here / Locked**.
- **Your current station is expanded** by default; the others collapse.
- **Locked steps** show what unlocks them: "Unlocks after *Get CI green*" (a link).
- **Filter:** All · Remaining · Done.

### 3.4 Home becomes "Today"

```
TODAY
Put it on the internet                        Station 7 · Deploy · ~90 min
You'll work in: Terminal · Your host
[ Continue → ]   What happens next: you deploy, we call /health, you're live.

LAST CHECK   ✕ Not yet: GET /health returned 404 (2 h ago)   [ See what to fix ]

YOUR PROGRESS   ▓▓▓▓▓▓▓░░░  7 of 10 steps   ·  Roles: Founder ✓ PM ✓ … DevOps (now)
                Labelled segments; hover = step name; click a role → that station
```

- **One card: the next step.** It shows *where you'll work* and *what happens after*.
- **Your last check result**, if one is failing, with a direct link to the fix.
- **Progress with labels**:
  - each segment of the Line has a tooltip and a link;
  - roles link to their station (fixes #3).

---

## 4. Teaching the model (comprehension)

### 4.1 First-run guided tour (once, skippable, replayable from Help)

Four coachmarks on the real UI after onboarding:

1. **"This is your next step."** The Continue button always takes you to it.
2. **"Work happens in your own tools."** Steps tell you where. Onefold checks the result.
3. **"Check my work."** We test what you built and tell you exactly what we saw. Failing is normal: read "What we got", fix, check again.
4. **"Your path."** Nine stations, one per role. Locked steps open as you go, and you can read ahead any time.

Rules:
- Each coachmark is focus-trapped, can be closed with Esc, and states "1 of 4".
- It respects reduced motion.
- Its completion is stored on the account, so it isn't shown again on another device.

### 4.2 "Before you start" checklist (Today, until it's done)

Five items, each with a one-line why and a link:
1. A GitHub account.
2. An editor installed.
3. Git installed (with a command to check: `git --version`).
4. A hosting account (the two supported providers).
5. 15 minutes for step 1.

Builders tick items off; it's dismissible. It answers "what do I need?" before step 1 instead of at Station 7.

### 4.3 Inline glossary

- **Terms get a dotted underline and a popover** the first few times they appear: *station, step, check, Line, verification token, ship*. Example: "**Check**: Onefold tests what you built (a URL, your repo, or your confirmation) and shows what it saw."
- **Help → Glossary** lists them all.

### 4.4 The step anatomy (the same on every step)

| Section | Purpose |
|---------|---------|
| **Goal** (1 sentence) | Why this step exists |
| **You'll work in** (chips) | Editor · Terminal · GitHub · Your host · Onefold |
| **You'll need** | Things from earlier steps, linked |
| **Do this** (numbered, tickable) | Ticks are saved per step: progress inside a step |
| **Done looks like** | A screenshot or snippet of the finished state |
| **What we check** | In plain words, *before* you press the button |
| **If it fails** | The 3 most common causes |

This is content work (Phase 4 of the main plan) plus a renderer: front-matter fields plus a Markdown convention, so writers fill a template. The renderer ships first; the 10 existing steps are migrated to it.

### 4.5 Check flow rewrite (fixes #5, #9)

**Button labels say what happens:**

| Check type | Button |
|------------|--------|
| attest | "Mark as done" (with the statement as a checkbox you tick first: "☐ My first version has three features or fewer") |
| http | "Check my live URL" |
| github | "Check my repo" |

**Results:**
- **While running:** "Calling https://… (2 s)" with a progress line, not "Queued…".
- **Passed:** a full-width success band.
  - It reads "✓ Done. You covered *Founder*" when the station is complete.
  - It offers a big **Next: <title>** button and moves focus to it.
  - A small Line animation fills the segment.
- **Failed:**
  - Opens on "What we got" and "Try this".
  - "Check again" stays put.
  - After 2 failures: "Still stuck? Read the troubleshooting guide / ask for help."

---

## 5. One vocabulary

| Concept | The only word we use | Retire |
|---------|----------------------|--------|
| Step you're on | **Current** | In progress, Now, Learning |
| Step you can start | **Next** | Up next, Available, Start |
| Can't start yet | **Locked** (always with "finish *X* first") | Ahead |
| Finished | **Done** | Covered, Passed (for steps) |
| Check outcome | **Passed / Not yet / Couldn't run** | Failed, ✕ |
| The main button | **Continue** (anywhere), **Start step** (first visit) | Start this step, Go to your current step |
| Station role finished | "You've covered *Role*" (used only in success moments) | — |

These live in one `copy.ts` so screens can't drift.

---

## 6. Help, recovery and empty states

- **Help page:**
  - How Onefold works (60-second read).
  - Glossary.
  - Replay the tour.
  - FAQ ("Where do I write code?", "My check fails", "Can I skip?", "Change my project").
  - Contact.
- **Stuck on a step for 3+ days** → a banner: "Stuck? Here's the troubleshooting guide, or skip for now" (skip is logged; checks still gate Ship).
- **Every empty state says what fills it and how**, e.g. Project with no URL: "You'll add this at Station 7: Deploy. Nothing to do yet."
- **The verification token is hidden until Station 6** (fixes #11). Before that, Project shows: name, idea, repo, plus "Live URL & token appear when you reach Deploy".

---

## 7. Phases

| Phase | Scope | Size | Fixes |
|-------|-------|------|-------|
| **UX-1: Navigation** | Top bar with labelled progress and a persistent Continue; Today/Path/Project/Help nav; step page breadcrumb, "Step n of N", station outline (desktop) and dropdown (phone); prev/next in header + J/K; one fixed bar on phones; ship moment inside the shell | ≈ 4–5 days | 7, 12, 13, part of 3 |
| **UX-2: Words** | `copy.ts` vocabulary; relabel every status and button; check buttons named by type; attest as a ticked statement; locked = "finish *X* first" with link | ≈ 2 days | 1, 2, 5, 8 |
| **UX-3: Teach** | First-run tour (4 coachmarks); "Before you start" checklist; glossary popovers + Help page; Line with labels/tooltips; roles link to stations | ≈ 4 days | 3, 4, 14 |
| **UX-4: Steps & checks** | Step anatomy renderer (goal, work-in chips, tickable "Do this", done-looks-like, what we check, if it fails); inline requirement fields in the action panel; success band + focus on Next; failure guidance after 2 tries; migrate the 10 steps | ≈ 5–6 days | 5, 6, 9, 11 |
| **UX-5: Path as a map** | Station cards with state and progress, current expanded, filter | ≈ 2 days | 10 |

**Order: UX-1 → UX-2 → UX-3 → UX-4 → UX-5.** UX-1 and UX-2 alone fix most of the "lost" feeling.

---

## 8. How we'll know it worked

**Usability test, before and after.** Run it with 5 people who have never seen Onefold. Each task is unassisted and think-aloud; a task passes when the person finishes it without help.

| Task | Pass if |
|------|---------|
| "You just signed up. Do the first thing the app wants." | Starts step 1 in < 60 s |
| "What does Onefold check when you press the button?" | Explains it in their own words |
| "Where would you write the code for this step?" | Says "my editor / terminal", not "in Onefold" |
| "Go to the step after next, then come back to where you were." | Done in ≤ 3 clicks each way |
| "Your Deploy check failed. Find out why and what to do." | Reads "What we got" and "Try this" without help |
| "How far through are you?" | Answers in < 10 s |

**Exit criteria:** 5/5 on the first and fourth tasks, ≥ 4/5 on the others.

**Analytics** (PostHog, from the main plan):
- Time from onboarding to the first step started.
- Share of sessions that hit Path → step → Path more than 3 times (a lost-user signal).
- Help opens per step.
- Check retries before a pass.

**Automated:**
- Playwright tests for each task above.
- The axe audits stay green.

---

## 9. Decisions for you

1. **Tour or no tour.** I recommend the 4-step tour; the alternative is a "How it works" page only.
2. **Is "Today" the right name for Home?** Alternatives: "Next step", "Dashboard".
3. **Hide the verification token until Deploy** (recommended), or keep it visible with an explanation?
