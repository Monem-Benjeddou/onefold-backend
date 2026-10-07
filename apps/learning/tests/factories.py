import itertools

from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.learning.models import Path, PathVersion, Station, Step

_counter = itertools.count(1)

HTTP_CHECK = {
    "kind": "http.get",
    "url": "{project.live_url}/health",
    "expect": {"status": 200, "body_contains": "{project.ownership_token}"},
}
ATTEST_CHECK = {"kind": "attest", "statement": "I did the thing."}


def make_user(**extra):
    n = next(_counter)
    return User.objects.create_user(email=f"builder{n}@example.com", **extra)


def api_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def make_path(slug="ship-your-first-product", published=True, stations=None):
    """
    Build a path directly in the DB. `stations` is a list of step lists:
    [[(slug, type, check_spec), ...], ...]. Defaults to a small 3-station path.
    """
    stations = stations or [
        [("problem", "build", None), ("scope-cut", "check", ATTEST_CHECK)],
        [("user-stories", "learn", None)],
        [("go-live", "ship", HTTP_CHECK)],
    ]
    path, _ = Path.objects.get_or_create(slug=slug, defaults={"title": "Ship it"})
    version = PathVersion.objects.create(
        path=path,
        version=f"0.0.{next(_counter)}",
        title="Ship it",
        content_hash="test",
        published_at=timezone.now() if published else None,
    )
    for s_order, steps in enumerate(stations, start=1):
        station = Station.objects.create(
            path_version=version,
            order=s_order,
            slug=f"station-{s_order}",
            title=f"Station {s_order}",
            role="Builder",
        )
        for order, (step_slug, step_type, check) in enumerate(steps, start=1):
            Step.objects.create(
                station=station,
                order=order,
                slug=step_slug,
                title=step_slug.replace("-", " ").title(),
                type=step_type,
                est_minutes=10,
                body_md="Do it.\n",
                check_spec=check,
            )
    return version
