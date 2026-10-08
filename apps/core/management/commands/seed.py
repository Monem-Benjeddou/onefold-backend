"""
Fill a development database with demo accounts at every stage of the path.

Safe to run on every start: existing accounts and their progress are left as
they are. Every demo account signs in with the password $SEED_DEMO_PASSWORD
(default "onefold"), or with one click from the login page in development.

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
from apps.core.demo import ADMIN_EMAIL, DEMO_DOMAIN, DEMO_STAGES, demo_email
from apps.learning import services as learning
from apps.learning.models import Path
from apps.projects.models import Project
from apps.verification.models import CheckRun

# (handle, name, pace, steps finished, project). "ship" = up to and including the
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
            self._passwords()

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

    def _passwords(self):
        """Give demo builders a password (and a confirmed email) if they lack one."""
        password = os.environ.get("SEED_DEMO_PASSWORD", "onefold")
        for handle in DEMO_STAGES:
            user = User.objects.filter(email=demo_email(handle)).first()
            if user and (not user.password or not user.has_usable_password()):
                user.set_password(password)
                user.email_verified_at = user.email_verified_at or timezone.now()
                user.save(update_fields=["password", "email_verified_at", "updated"])

    def _builder(self, version, handle, name, pace, finished, project_data):
        email = demo_email(handle)
        user, created = User.objects.get_or_create(
            email=email, defaults={"name": name, "email_verified_at": timezone.now()}
        )
        if not created or finished is None:
            return created

        enrollment, _ = learning.enroll(user, version, pace=pace)
        enrollment.experience = "often" if finished == "ship" else "once"
        enrollment.save(update_fields=["experience", "updated"])
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
        web_port = os.environ.get("WEB_PORT", "3000")
        api_port = os.environ.get("API_PORT", "8000")
        inbox_port = os.environ.get("MAILPIT_PORT", "8025")
        password = os.environ.get("SEED_DEMO_PASSWORD", "onefold")
        lines = [
            "Onefold is ready.",
            "",
            f"  App        http://localhost:{web_port}",
            f"  Inbox      http://localhost:{inbox_port}   (every email lands here)",
            f"  Admin      http://localhost:{api_port}/admin/   "
            f"{ADMIN_EMAIL} ({status[admin_created]})",
            f"  API docs   http://localhost:{api_port}/api/docs/",
            "",
            f"  Demo accounts (password: {password}, or one click on the login page):",
        ]
        for (handle, *_), was_created in zip(BUILDERS, created, strict=True):
            lines.append(
                f"    {demo_email(handle):<22} {DEMO_STAGES[handle]:<28} ({status[was_created]})"
            )
        width = max(len(line) for line in lines) + 2
        out.write("")
        out.write(self.style.SUCCESS("┌" + "─" * width + "┐"))
        for line in lines:
            out.write(self.style.SUCCESS("│ ") + line.ljust(width - 1) + self.style.SUCCESS("│"))
        out.write(self.style.SUCCESS("└" + "─" * width + "┘"))
        out.write("")
