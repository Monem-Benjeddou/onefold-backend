import pytest

from apps.learning import services
from apps.learning.tests.factories import api_client, make_path, make_user
from apps.projects.models import Project

pytestmark = pytest.mark.django_db

BASE = "/api/v1/projects/"


@pytest.fixture
def user():
    return make_user()


@pytest.fixture
def client(user):
    return api_client(user)


def test_create_assigns_slug_token_and_enrollment(client, user):
    enrollment, _ = services.enroll(user, make_path())

    response = client.post(
        BASE,
        {
            "name": "Habit Loop!",
            "idea": "Help people keep one habit.",
            "repo_full_name": "https://github.com/ada/habit-loop.git",
            "live_url": "https://habit-loop.example.com/",
        },
    )

    assert response.status_code == 201, response.json()
    data = response.json()
    assert data["slug"] == "habit-loop"
    assert data["repo_full_name"] == "ada/habit-loop"
    assert data["live_url"] == "https://habit-loop.example.com"
    assert data["visibility"] == "unlisted"
    assert data["ownership_token"].startswith("onefold-verify-")
    assert data["enrollment"] == str(enrollment.pk)


def test_slugs_are_unique_per_user(client):
    first = client.post(BASE, {"name": "Habit Loop"}).json()
    second = client.post(BASE, {"name": "Habit Loop"}).json()
    assert (first["slug"], second["slug"]) == ("habit-loop", "habit-loop-2")


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("live_url", "http://habit-loop.example.com", "https://"),
        ("live_url", "https://ada:secret@habit-loop.example.com", "username and password"),
        ("repo_full_name", "not a repo", "owner/repo"),
        ("name", "!!!", "letter or number"),
    ],
)
def test_validation_messages(client, field, value, message):
    payload = {"name": "Habit Loop", field: value}
    response = client.post(BASE, payload)
    assert response.status_code == 400
    assert message in str(response.json())


def test_token_and_slug_are_read_only(client):
    project = client.post(BASE, {"name": "Habit Loop"}).json()
    response = client.patch(
        f"{BASE}{project['id']}/", {"ownership_token": "mine", "slug": "x", "visibility": "public"}
    )
    assert response.status_code == 200
    assert response.json()["ownership_token"] == project["ownership_token"]
    assert response.json()["slug"] == "habit-loop"
    assert response.json()["visibility"] == "public"


def test_other_builders_projects_are_invisible(client):
    theirs = Project.objects.create(user=make_user(), name="Secret", slug="secret")

    assert client.get(BASE).json()["count"] == 0
    assert client.get(f"{BASE}{theirs.pk}/").status_code == 404
    assert client.patch(f"{BASE}{theirs.pk}/", {"name": "Mine"}).status_code == 404
    assert client.delete(f"{BASE}{theirs.pk}/").status_code == 404
