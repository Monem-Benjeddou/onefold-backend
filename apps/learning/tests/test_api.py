import pytest
from rest_framework.test import APIClient

from .factories import api_client, make_path, make_user

pytestmark = pytest.mark.django_db

BASE = "/api/v1/learning"


@pytest.fixture
def client():
    make_path()
    return api_client(make_user())


def test_requires_authentication():
    response = APIClient().get(f"{BASE}/paths/current/")
    assert response.status_code in (401, 403)


def test_current_path_outline(client):
    response = client.get(f"{BASE}/paths/current/")

    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "ship-your-first-product"
    assert [s["order"] for s in data["stations"]] == [1, 2, 3]
    assert data["stations"][0]["steps"][1] == {
        "slug": "scope-cut",
        "title": "Scope Cut",
        "type": "check",
        "est_minutes": 10,
        "requires_laptop": False,
        "has_check": True,
    }
    assert "body_md" not in data["stations"][0]["steps"][0]


def test_no_published_path_is_a_404():
    response = api_client(make_user()).get(f"{BASE}/paths/current/")
    assert response.status_code == 404


def test_enroll_then_read_enrollment(client):
    assert client.get(f"{BASE}/enrollment/").status_code == 404

    created = client.post(f"{BASE}/enrollment/", {"pace": "2-4"})
    again = client.post(f"{BASE}/enrollment/", {})

    assert created.status_code == 201
    assert again.status_code == 200
    assert again.json()["id"] == created.json()["id"]

    data = client.get(f"{BASE}/enrollment/").json()
    assert data["pace"] == "2-4"
    assert data["totals"] == {"done": 0, "total": 4}
    assert data["next_step"]["slug"] == "problem"
    assert data["next_step"]["station_title"] == "Station 1"


def test_invalid_pace_is_rejected(client):
    assert client.post(f"{BASE}/enrollment/", {"pace": "always"}).status_code == 400


def test_step_flow(client):
    client.post(f"{BASE}/enrollment/", {})

    detail = client.get(f"{BASE}/enrollment/steps/problem/")
    assert detail.status_code == 200
    assert detail.json()["body_md"] == "Do it.\n"
    assert detail.json()["station"]["order"] == 1
    assert detail.json()["check"] is None

    gate = client.get(f"{BASE}/enrollment/steps/go-live/").json()["check"]
    assert gate == {
        "kind": "http.get",
        "url": "{project.live_url}/health",
        "expect_status": 200,
        "expect_body_contains": "{project.ownership_token}",
    }
    assert client.get(f"{BASE}/enrollment/steps/scope-cut/").json()["check"] == {
        "kind": "attest",
        "statement": "I did the thing.",
    }

    started = client.post(f"{BASE}/enrollment/steps/problem/start/")
    assert started.json()["status"] == "in_progress"

    done = client.post(f"{BASE}/enrollment/steps/problem/complete/")
    assert done.json()["status"] == "done"

    enrollment = client.get(f"{BASE}/enrollment/").json()
    assert enrollment["totals"]["done"] == 1
    assert enrollment["next_step"]["slug"] == "scope-cut"


def test_conflicts_carry_a_code(client):
    client.post(f"{BASE}/enrollment/", {})

    locked = client.post(f"{BASE}/enrollment/steps/user-stories/start/")
    assert locked.status_code == 409

    client.post(f"{BASE}/enrollment/steps/problem/complete/")
    gated = client.post(f"{BASE}/enrollment/steps/scope-cut/complete/")
    assert gated.status_code == 409
    assert "Check my work" in str(gated.json())


def test_resume_position_is_saved(client):
    client.post(f"{BASE}/enrollment/", {})

    saved = client.patch(f"{BASE}/enrollment/steps/problem/", {"last_position": 1240})
    assert saved.status_code == 200
    assert client.get(f"{BASE}/enrollment/").json()["next_step"]["last_position"] == 1240

    assert client.patch(f"{BASE}/enrollment/steps/problem/", {}).status_code == 400


def test_unknown_step_is_a_404(client):
    client.post(f"{BASE}/enrollment/", {})
    assert client.get(f"{BASE}/enrollment/steps/nope/").status_code == 404
