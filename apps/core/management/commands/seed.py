"""
Fill a development database with demo accounts at every stage of the path.

Safe to run on every start: existing accounts and their progress are left as
they are. Each run prints fresh sign-in links (valid 24 hours) so you can open
any account in the web app straight away.

    python manage.py seed               # runs on `docker compose up`
    python manage.py seed --reset       # wipe demo accounts and recreate them
"""

import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import issue_link
from apps.learning import services as learning
from apps.learning.models import Path
from apps.projects.models import Project
from apps.verification.models import CheckRun

DEMO_DOMAIN = "onefold.local"
ADMIN_EMAIL = f"admin@{DEMO_DOMAIN}"
LINK_TTL_MINUTES = 60 * 24

# (email, name, pace, steps finished, project). "ship" = up to and including the
# first Ship step, "deploy" = everything before it; None = not onboarded yet.
BUILDERS = [
    ("new", "", "", None, None),
    (
        "ada",
        "Ada",
        "5-8",
        1,
        {"name": "Habit Loop", "idea": "Help people keep one daily habit without guilt."},
    ),
    (
        "grace",
        "Grace",
        "10+",
        "deploy",
        {
            "name": "Invoice Nudge",
            "idea": "Chase late invoices for freelancers without the awkward emails.",
            "repo_full_name": "grace/invoice-nudge",
            "live_url": "https://invoice-nudge.example.com",
        },
    ),
    (
        "linus",
        "Linus",
        "10+",
        "ship",
        {
            "name": "Pair Up",
            "idea": "Match people who want to learn the same thing this week.",
            "repo_full_name": "linus/pair-up",
            "live_url": "https://pair-up.example.com",
            "visibility": "public",
        },
    ),
]


class Command(BaseCommand):
    help = "Create demo accounts and data for local development (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true", help="Delete demo accounts first, then recreate."
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow running with DEBUG off (never in production).",
        )

    def handle(self, *args, reset=False, force=False, **options):
        if not settings.DEBUG and not force:
            raise CommandError(
                "Refusing to seed with DEBUG off. Demo accounts don't belong in production."
            )

        version = self._published_version()
        with transaction.atomic():
            if reset:
                deleted, _ = User.objects.filter(email__endswith=f"@{DEMO_DOMAIN}").delete()
                self.stdout.write(f"Removed demo data ({deleted} rows).")
            admin_created = self._admin()
            created = [self._builder(version, *builder) for builder in BUILDERS]

        self._report(admin_created, created)

    def _published_version(self):
        path = Path.objects.filter(slug=settings.LEARNING_DEFAULT_PATH).first()
        version = path.latest_published_version() if path else None
        if version is None:
            call_command("sync_content", publish=True, stdout=self.stdout)
            version = Path.objects.get(
                slug=settings.LEARNING_DEFAULT_PATH
            ).latest_published_version()
        return version

    def _admin(self):
        if User.objects.filter(email=ADMIN_EMAIL).exists():
            return False
        User.objects.create_superuser(
            ADMIN_EMAIL, os.environ.get("SEED_ADMIN_PASSWORD", "onefold"), name="Admin"
        )
        return True

    def _builder(self, version, handle, name, pace, finished, project_data):
        email = f"{handle}@{DEMO_DOMAIN}"
        user, created = User.objects.get_or_create(email=email, defaults={"name": name})
        if not created or finished is None:
            return created

        enrollment, _ = learning.enroll(user, version, pace=pace)
        project = Project.objects.create(
            user=user,
            enrollment=enrollment,
            slug=project_data["name"].lower().replace(" ", "-"),
            **project_data,
        )

        progress = list(enrollment.progress.select_related("step__station"))
        if finished in ("ship", "deploy"):
            ship_index = next(i for i, p in enumerate(progress) if p.step.type == "ship")
            finished = ship_index + 1 if finished == "ship" else ship_index
        for item in progress[:finished]:
            if item.step.has_check:
                self._check_run(project, item, passed=True)
            learning.complete_step(item, verified=True)

        # Grace is at Deploy with one failed attempt: her app answers 404.
        current = learning.next_progress(enrollment)
        if (
            handle == "grace"
            and current
            and (current.step.check_spec or {}).get("kind") == "http.get"
        ):
            learning.start_step(current)
            self._check_run(project, current, passed=False)
        return created

    def _check_run(self, project, progress, passed):
        spec = progress.step.check_spec
        if spec["kind"] == "attest":
            got = {}
            checked = f"You confirmed: {spec['statement']}"
        else:
            got = (
                {"status": 200, "reason": "OK", "elapsed_ms": 84, "body_excerpt": '{"ok": true}'}
                if passed
                else {
                    "status": 404,
                    "reason": "Not Found",
                    "elapsed_ms": 61,
                    "body_excerpt": "Not Found",
                }
            )
            checked = (
                f"GET {project.live_url or '<live URL>'}/health returns 200 and contains your token"
            )
        now = timezone.now()
        CheckRun.objects.create(
            project=project,
            step=progress.step,
            kind=spec["kind"],
            spec=spec,
            status=CheckRun.Status.PASSED if passed else CheckRun.Status.FAILED,
            result={
                "passed": passed,
                "checked": checked,
                "got": got,
                "reasons": [] if passed else ["Expected status 200, got 404."],
                "hints": []
                if passed
                else [
                    "The route doesn't exist on your deployed app. Is the latest commit deployed?"
                ],
            },
            duration_ms=got.get("elapsed_ms", 3),
            started_at=now,
            finished_at=now,
        )

    def _report(self, admin_created, created):
        out = self.stdout
        status = {True: "created", False: "exists"}
        out.write("")
        out.write(self.style.SUCCESS("Demo data ready."))
        api_port = os.environ.get("API_PORT", "8000")
        out.write(
            f"  Admin  {ADMIN_EMAIL}  ({status[admin_created]})  → http://localhost:{api_port}/admin/"
        )
        if admin_created:
            out.write("         password: $SEED_ADMIN_PASSWORD (default: onefold)")
        out.write("")
        out.write("  Sign-in links for the web app (single use, valid 24 hours):")
        stages = {
            "new": "signed up, not onboarded",
            "ada": "just started, station 1",
            "grace": "at Deploy, a failed check",
            "linus": "shipped, live URL",
        }
        for (handle, *_), was_created in zip(BUILDERS, created, strict=True):
            email = f"{handle}@{DEMO_DOMAIN}"
            link = issue_link(email, ttl_minutes=LINK_TTL_MINUTES)
            out.write(f"  {email:<22} {stages[handle]:<26} ({status[was_created]})")
            out.write(f"    {link}")
        out.write("")
