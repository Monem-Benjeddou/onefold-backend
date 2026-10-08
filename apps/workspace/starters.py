"""Starter projects offered at the end of onboarding."""

STARTERS = [
    {
        "slug": "habit-loop",
        "name": "Habit Loop",
        "idea": "Help people keep one daily habit without guilt.",
        "summary": "A daily check-in with streaks. Auth, one core table, a dashboard.",
        "builds": ["Accounts", "Daily check-ins", "Streaks"],
    },
    {
        "slug": "waitlist-saas",
        "name": "Waitlist",
        "idea": "Let a founder collect sign-ups for a launch and email them when it's ready.",
        "summary": "A public sign-up page, an admin list and a launch email. Real users on day one.",
        "builds": ["Public page", "Admin list", "Transactional email"],
    },
    {
        "slug": "link-in-bio",
        "name": "Link Page",
        "idea": "Give anyone a fast, good-looking page with all their links.",
        "summary": "Public profile pages with an editor and click counts. Great for a first deploy.",
        "builds": ["Public profiles", "Editor", "Click analytics"],
    },
]

STARTER_SLUGS = [starter["slug"] for starter in STARTERS]
OWN_IDEA = "own"
