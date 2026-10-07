import re
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.accounts.models import MagicLink, User
from apps.learning.models import Enrollment
from apps.verification.models import CheckRun

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def debug_on(settings):
    # Django turns DEBUG off for tests; the seeder only runs in development.
    settings.DEBUG = True


def seed(*args):
    out = StringIO()
    call_command("seed", *args, stdout=out)
    return out.getvalue()


def statuses(email):
    enrollment = Enrollment.objects.get(user__email=email)
    return [p.status for p in enrollment.progress.order_by("step__station__order", "step__order")]


def test_seed_creates_every_stage():
    output = seed()

    admin = User.objects.get(email="admin@onefold.local")
    assert admin.is_superuser and admin.check_password("onefold")

    new = User.objects.get(email="new@onefold.local")
    assert not new.enrollments.exists()

    assert statuses("ada@onefold.local")[:2] == ["done", "available"]

    grace = statuses("grace@onefold.local")
    assert grace.index("in_progress") == grace.count("done")  # sitting on Deploy
    failed = CheckRun.objects.get(project__user__email="grace@onefold.local", status="failed")
    assert failed.step.slug == "go-live"
    assert failed.result["got"]["status"] == 404

    linus = User.objects.get(email="linus@onefold.local")
    assert linus.projects.get().live_url == "https://pair-up.example.com"
    go_live = linus.enrollments.get().progress.get(step__slug="go-live")
    assert go_live.status == "done"

    # Fresh sign-in links for each builder, valid for a day.
    assert len(re.findall(r"/auth/verify\?token=", output)) == 4
    assert MagicLink.objects.count() == 4


def test_seed_is_idempotent():
    seed()
    counts = (User.objects.count(), Enrollment.objects.count(), CheckRun.objects.count())
    output = seed()
    assert (User.objects.count(), Enrollment.objects.count(), CheckRun.objects.count()) == counts
    assert "(exists)" in output


def test_admin_password_from_environment(monkeypatch):
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "s3cret-pass")
    seed()
    assert User.objects.get(email="admin@onefold.local").check_password("s3cret-pass")


def test_reset_recreates_demo_accounts_only():
    seed()
    real = User.objects.create_user("real@example.com")
    User.objects.filter(email="ada@onefold.local").update(name="Changed")

    seed("--reset")

    assert User.objects.get(email="ada@onefold.local").name == "Ada"
    assert User.objects.filter(pk=real.pk).exists()


def test_refuses_without_debug(settings):
    settings.DEBUG = False
    with pytest.raises(CommandError, match="DEBUG off"):
        seed()
