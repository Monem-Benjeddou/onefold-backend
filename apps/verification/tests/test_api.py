from unittest import mock

import pytest

from apps.learning import services as learning
from apps.learning.tests.factories import api_client, make_path, make_user
from apps.projects.models import Project
from apps.verification import net, services
from apps.verification.models import CheckRun

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup():
    user = make_user()
    enrollment, _ = learning.enroll(user, make_path())
    project = Project.objects.create(
        user=user,
        enrollment=enrollment,
        name="Habit Loop",
        slug="habit-loop",
        live_url="https://habit-loop.example.com",
    )
    return user, enrollment, project


def finish(enrollment, *slugs):
    for slug in slugs:
        learning.complete_step(learning.get_progress(enrollment, slug), verified=True)


def checks_url(project):
    return f"/api/v1/projects/{project.pk}/checks/"


def ok_response(project):
    return net.FetchResult(
        status=200,
        reason="OK",
        headers={},
        body=f"alive {project.ownership_token}".encode(),
        truncated=False,
        elapsed_ms=12,
        ip="93.184.216.34",
    )


class TestRequestCheck:
    def test_queues_and_runs_after_commit(self, setup, django_capture_on_commit_callbacks):
        user, enrollment, project = setup
        finish(enrollment, "problem")
        client = api_client(user)

        with mock.patch("apps.verification.views.run_check_task.delay") as delay:
            with django_capture_on_commit_callbacks(execute=True):
                response = client.post(checks_url(project), {"step": "scope-cut"})

        assert response.status_code == 202
        run_id = response.json()["id"]
        assert response.json()["status"] == "queued"
        delay.assert_called_once_with(run_id)
        # Requesting a check starts the step.
        assert learning.get_progress(enrollment, "scope-cut").status == "in_progress"

    def test_idempotency_key_returns_the_same_run(self, setup):
        user, enrollment, project = setup
        finish(enrollment, "problem")
        client = api_client(user)

        with mock.patch("apps.verification.views.run_check_task.delay"):
            first = client.post(
                checks_url(project), {"step": "scope-cut"}, HTTP_IDEMPOTENCY_KEY="k1"
            )
            again = client.post(
                checks_url(project), {"step": "scope-cut"}, HTTP_IDEMPOTENCY_KEY="k1"
            )

        assert (first.status_code, again.status_code) == (202, 200)
        assert first.json()["id"] == again.json()["id"]
        assert CheckRun.objects.count() == 1

    @pytest.mark.parametrize(
        "step, status, code",
        [
            ("scope-cut", 409, "step_locked"),
            ("problem", 409, "no_check"),
            ("missing", 404, "step_not_found"),
        ],
    )
    def test_rejections(self, setup, step, status, code):
        user, _, project = setup
        with pytest.raises(services.CheckRequestError) as exc:
            services.request_check(project, step)
        assert (exc.value.status, exc.value.code) == (status, code)

        response = api_client(user).post(checks_url(project), {"step": step})
        assert response.status_code == status

    def test_preflight_explains_what_is_missing(self, setup):
        user, enrollment, project = setup
        finish(enrollment, "problem", "scope-cut", "user-stories")
        project.live_url = ""
        project.save()

        response = api_client(user).post(checks_url(project), {"step": "go-live"})

        assert response.status_code == 400
        assert "Add your live URL" in str(response.json())

    def test_rate_limited(self, setup, settings):
        settings.VERIFICATION_CHECKS_PER_MINUTE = 2
        _, enrollment, project = setup
        finish(enrollment, "problem")
        services.request_check(project, "scope-cut")
        services.request_check(project, "scope-cut")

        with pytest.raises(services.CheckRequestError) as exc:
            services.request_check(project, "scope-cut")
        assert exc.value.status == 429

    def test_other_builders_project_is_a_404(self, setup):
        _, _, project = setup
        response = api_client(make_user()).post(checks_url(project), {"step": "scope-cut"})
        assert response.status_code == 404


class TestRunCheck:
    def test_attest_passes_and_unlocks_the_next_step(self, setup):
        _, enrollment, project = setup
        finish(enrollment, "problem")
        run, _ = services.request_check(project, "scope-cut")

        run = services.run_check(run.pk)

        assert run.status == "passed"
        assert run.duration_ms is not None and run.finished_at
        assert "You confirmed" in run.result["checked"]
        assert learning.get_progress(enrollment, "scope-cut").status == "done"
        assert learning.get_progress(enrollment, "user-stories").status == "available"

    def test_http_check_end_to_end(self, setup):
        user, enrollment, project = setup
        finish(enrollment, "problem", "scope-cut", "user-stories")
        run, _ = services.request_check(project, "go-live")

        with mock.patch.object(net, "fetch", return_value=ok_response(project)):
            services.run_check(run.pk)

        detail = api_client(user).get(f"/api/v1/checks/{run.pk}/").json()
        assert detail["status"] == "passed"
        assert detail["step"] == "go-live"
        assert detail["result"]["got"]["status"] == 200
        assert learning.get_progress(enrollment, "go-live").status == "done"

    def test_failure_leaves_the_step_open(self, setup):
        _, enrollment, project = setup
        finish(enrollment, "problem", "scope-cut", "user-stories")
        run, _ = services.request_check(project, "go-live")

        with mock.patch.object(net, "fetch", side_effect=net.FetchError("No response within 5s")):
            run = services.run_check(run.pk)

        assert run.status == "failed"
        assert run.result["reasons"] == ["No response within 5s"]
        assert learning.get_progress(enrollment, "go-live").status == "in_progress"

    def test_our_crash_is_an_error_not_a_failure(self, setup):
        _, enrollment, project = setup
        finish(enrollment, "problem", "scope-cut", "user-stories")
        run, _ = services.request_check(project, "go-live")

        with mock.patch.object(net, "fetch", side_effect=RuntimeError("bug")):
            run = services.run_check(run.pk)

        assert run.status == "error"
        assert "on us" in run.result["reasons"][0]

    def test_running_twice_executes_once(self, setup):
        _, enrollment, project = setup
        finish(enrollment, "problem")
        run, _ = services.request_check(project, "scope-cut")

        services.run_check(run.pk)
        with mock.patch.object(services, "get_executor") as get_executor:
            again = services.run_check(run.pk)

        get_executor.assert_not_called()
        assert again.status == "passed"

    def test_runs_list_is_filterable_and_private(self, setup):
        user, enrollment, project = setup
        finish(enrollment, "problem")
        services.request_check(project, "scope-cut")
        client = api_client(user)

        assert client.get(checks_url(project)).json()["count"] == 1
        assert client.get(checks_url(project), {"step": "go-live"}).json()["count"] == 0
        run = CheckRun.objects.get()
        assert api_client(make_user()).get(f"/api/v1/checks/{run.pk}/").status_code == 404
