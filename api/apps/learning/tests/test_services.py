from pathlib import Path

import pytest
from django.conf import settings

from apps.learning import services
from apps.learning.content import load_path
from apps.learning.models import Enrollment, PathVersion, StepProgress

from .factories import make_path, make_user

pytestmark = pytest.mark.django_db

DRAFT = Path(settings.LEARNING_CONTENT_DIR) / "paths" / "ship-your-first-product"


def statuses(enrollment):
    return [p.status for p in enrollment.progress.order_by("step__station__order", "step__order")]


class TestSyncPath:
    def test_creates_then_is_idempotent(self):
        spec = load_path(DRAFT)

        version, created = services.sync_path(spec, publish=True)
        again, created_again = services.sync_path(spec, publish=True)

        assert created and not created_again
        assert again.pk == version.pk
        assert version.is_published
        assert version.stations.count() == 9
        assert PathVersion.objects.count() == 1

    def test_published_versions_are_immutable(self):
        spec = load_path(DRAFT)
        services.sync_path(spec)
        spec.content_hash = "something-else"

        with pytest.raises(services.ImmutableVersionError, match="Bump the version"):
            services.sync_path(spec)

    def test_draft_can_be_published_later(self):
        spec = load_path(DRAFT)
        version, _ = services.sync_path(spec)
        assert not version.is_published

        version, _ = services.sync_path(spec, publish=True)
        assert version.is_published


class TestEnrollment:
    def test_enroll_opens_only_the_first_step(self):
        enrollment, created = services.enroll(make_user(), make_path(), pace="5-8")

        assert created
        assert enrollment.pace == "5-8"
        assert statuses(enrollment) == ["available", "locked", "locked", "locked"]

    def test_enrolling_twice_returns_the_active_enrollment(self):
        user, version = make_user(), make_path()
        first, _ = services.enroll(user, version)
        second, created = services.enroll(user, version)

        assert not created and second.pk == first.pk
        assert Enrollment.objects.filter(user=user).count() == 1

    def test_cannot_enroll_in_an_unpublished_path(self):
        with pytest.raises(services.ProgressError) as exc:
            services.enroll(make_user(), make_path(published=False))
        assert exc.value.code == "path_unpublished"


class TestProgress:
    @pytest.fixture
    def enrollment(self):
        return services.enroll(make_user(), make_path())[0]

    def test_complete_unlocks_the_next_step(self, enrollment):
        first = services.get_progress(enrollment, "problem")
        services.complete_step(first)

        first.refresh_from_db()
        assert first.status == "done" and first.completed_at and first.started_at
        assert statuses(enrollment) == ["done", "available", "locked", "locked"]

    def test_complete_is_idempotent(self, enrollment):
        first = services.get_progress(enrollment, "problem")
        services.complete_step(first)
        services.complete_step(first)
        assert statuses(enrollment) == ["done", "available", "locked", "locked"]

    def test_locked_steps_cannot_start_or_complete(self, enrollment):
        locked = services.get_progress(enrollment, "user-stories")
        for action in (services.start_step, services.complete_step):
            with pytest.raises(services.ProgressError) as exc:
                action(locked)
            assert exc.value.code == "step_locked"

    def test_checked_steps_need_a_passing_check(self, enrollment):
        services.complete_step(services.get_progress(enrollment, "problem"))
        gated = services.get_progress(enrollment, "scope-cut")

        with pytest.raises(services.ProgressError) as exc:
            services.complete_step(gated)
        assert exc.value.code == "check_required"

        services.complete_step(gated, verified=True)
        assert services.get_progress(enrollment, "user-stories").status == "available"

    def test_next_progress_prefers_the_step_in_progress(self, enrollment):
        assert services.next_progress(enrollment).step.slug == "problem"
        services.complete_step(services.get_progress(enrollment, "problem"))
        services.start_step(services.get_progress(enrollment, "scope-cut"))

        upcoming = services.next_progress(enrollment)
        assert upcoming.step.slug == "scope-cut"
        assert upcoming.status == StepProgress.Status.IN_PROGRESS
