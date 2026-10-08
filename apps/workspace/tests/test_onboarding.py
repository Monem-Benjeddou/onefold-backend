from unittest import mock

import pytest

from apps.learning.models import Enrollment
from apps.learning.tests.factories import api_client, make_path, make_user
from apps.projects.models import Project
from apps.workspace.models import OnboardingDraft

pytestmark = pytest.mark.django_db

ANSWERS = {
    "idea": "Chase late invoices without the awkward emails.",
    "pace": "5-8",
    "experience": "once",
    "starter": "own",
    "project_name": "Invoice Nudge",
    "project_idea": "",
}


@pytest.fixture
def user():
    make_path()
    return make_user()


@pytest.fixture
def client(user):
    return api_client(user)


def test_new_builders_start_at_step_one_with_choices(client):
    data = client.get("/api/v1/onboarding/").json()
    assert data["complete"] is False
    assert data["step"] == 1
    assert data["draft"] == {}
    assert [s["slug"] for s in data["starters"]] == ["habit-loop", "waitlist-saas", "link-in-bio"]
    assert [p["value"] for p in data["paces"]] == ["2-4", "5-8", "10+"]
    assert [e["value"] for e in data["experiences"]] == ["never", "once", "often"]


def test_draft_survives_and_only_keeps_known_short_fields(client):
    response = client.put(
        "/api/v1/onboarding/draft/",
        {"step": 3, "data": {"idea": "x" * 500, "pace": "2-4", "evil": "nope", "n": 1}},
        format="json",
    )
    assert response.status_code == 204
    data = client.get("/api/v1/onboarding/").json()
    assert data["step"] == 3
    assert data["draft"] == {"idea": "x" * 300, "pace": "2-4"}


def test_finishing_enrolls_and_creates_the_project_in_one_go(client, user):
    client.put("/api/v1/onboarding/draft/", {"step": 4, "data": {"pace": "5-8"}}, format="json")

    response = client.post("/api/v1/onboarding/", ANSWERS, format="json")

    assert response.status_code == 201
    project = Project.objects.get(user=user)
    assert project.name == "Invoice Nudge"
    assert project.idea == ANSWERS["idea"]  # own idea comes from step 1
    enrollment = Enrollment.objects.get(user=user)
    assert (enrollment.pace, enrollment.experience) == ("5-8", "once")
    assert project.enrollment == enrollment
    assert not OnboardingDraft.objects.exists()
    assert client.get("/api/v1/onboarding/").json()["complete"] is True
    assert client.get("/api/v1/auth/me/").json()["onboarding_complete"] is True


def test_finishing_twice_is_safe(client, user):
    assert client.post("/api/v1/onboarding/", ANSWERS, format="json").status_code == 201
    again = client.post("/api/v1/onboarding/", {**ANSWERS, "project_name": "Other"}, format="json")
    assert again.status_code == 200
    assert Project.objects.filter(user=user).count() == 1
    assert Enrollment.objects.filter(user=user).count() == 1


def test_a_starter_fills_in_the_idea(client, user):
    client.post(
        "/api/v1/onboarding/",
        {**ANSWERS, "starter": "habit-loop", "project_name": "Habit Loop", "idea": ""},
        format="json",
    )
    assert Project.objects.get(user=user).idea == "Help people keep one daily habit without guilt."


def test_own_idea_needs_an_idea(client):
    response = client.post(
        "/api/v1/onboarding/", {**ANSWERS, "idea": "", "project_idea": ""}, format="json"
    )
    assert response.status_code == 400
    assert "project_idea" in response.json()


def test_validation_errors_point_at_fields(client):
    response = client.post(
        "/api/v1/onboarding/", {**ANSWERS, "pace": "1h", "project_name": "!!!"}, format="json"
    )
    assert response.status_code == 400
    assert {"pace", "project_name"} <= set(response.json())


def test_a_failure_halfway_leaves_nothing_behind(client, user):
    with mock.patch("apps.workspace.services.Project.objects.create", side_effect=RuntimeError):
        with pytest.raises(RuntimeError):
            client.post("/api/v1/onboarding/", ANSWERS, format="json")
    assert not Enrollment.objects.filter(user=user).exists()
    assert client.post("/api/v1/onboarding/", ANSWERS, format="json").status_code == 201


def test_enrolled_without_a_project_is_not_onboarded(client, user):
    # The old two-call flow could leave builders here; they go back to onboarding.
    client.post("/api/v1/learning/enrollment/", {"pace": "5-8"}, format="json")
    assert client.get("/api/v1/workspace/").json()["onboarding_complete"] is False
    response = client.post("/api/v1/onboarding/", ANSWERS, format="json")
    assert response.status_code == 201
    assert client.get("/api/v1/workspace/").json()["onboarding_complete"] is True


def test_workspace_in_one_call(client):
    empty = client.get("/api/v1/workspace/").json()
    assert empty["enrollment"] is None and empty["project"] is None
    assert empty["user"]["onboarding_complete"] is False

    client.post("/api/v1/onboarding/", ANSWERS, format="json")
    data = client.get("/api/v1/workspace/").json()
    assert data["onboarding_complete"] is True
    assert data["project"]["name"] == "Invoice Nudge"
    assert data["enrollment"]["next_step"]["slug"] == "problem"


def test_step_detail_links_previous_and_next(client):
    client.post("/api/v1/onboarding/", ANSWERS, format="json")
    first = client.get("/api/v1/learning/enrollment/steps/problem/").json()
    assert first["previous"] is None
    assert first["next"] == {"slug": "scope-cut", "title": "Scope Cut", "status": "locked"}
    # Locked steps can be read ahead.
    last = client.get("/api/v1/learning/enrollment/steps/go-live/")
    assert last.status_code == 200
    assert last.json()["status"] == "locked"
    assert last.json()["next"] is None
    assert last.json()["previous"]["slug"] == "user-stories"
