"""Demo accounts for local development (see the `seed` command)."""

DEMO_DOMAIN = "onefold.local"
ADMIN_EMAIL = f"admin@{DEMO_DOMAIN}"

# handle -> what that account shows off. Order is the order on the login page.
DEMO_STAGES = {
    "new": "Signed up, not onboarded",
    "ada": "Just started, station 1",
    "grace": "At Deploy, one failed check",
    "linus": "Shipped, live URL",
}


def demo_email(handle):
    return f"{handle}@{DEMO_DOMAIN}"
