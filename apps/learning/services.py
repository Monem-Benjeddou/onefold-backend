"""
Business rules for paths, enrollments and step progress.

Progress is linear: finishing (or skipping) a step makes the next one
available. Steps with a ``check_spec`` can only be finished by a passing
check, via ``complete_step(..., verified=True)``.
"""

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Enrollment, Path, PathVersion, Station, Step, StepProgress


class ProgressError(Exception):
    """A progress transition that the rules don't allow."""

    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


class ImmutableVersionError(Exception):
    pass


# --- Content sync -----------------------------------------------------------


@transaction.atomic
def sync_path(spec, publish=False):
    """
    Store a parsed PathSpec as a PathVersion.

    Returns ``(path_version, created)``. Re-syncing identical content is a no-op;
    changing content without bumping the version raises ImmutableVersionError,
    because builders may already be enrolled in that version.
    """
    path, _ = Path.objects.get_or_create(slug=spec.slug, defaults={"title": spec.title})
    if path.title != spec.title:
        path.title = spec.title
        path.save(update_fields=["title", "updated"])

    existing = PathVersion.objects.filter(path=path, version=spec.version).first()
    if existing:
        if existing.content_hash != spec.content_hash:
            raise ImmutableVersionError(
                f"{spec.slug}@{spec.version} already exists with different content. "
                "Bump the version in path.yml."
            )
        if publish and not existing.is_published:
            existing.published_at = timezone.now()
            existing.save(update_fields=["published_at", "updated"])
        return existing, False

    version = PathVersion.objects.create(
        path=path,
        version=spec.version,
        title=spec.title,
        outcome=spec.outcome,
        content_hash=spec.content_hash,
        published_at=timezone.now() if publish else None,
    )
    for station_spec in spec.stations:
        station = Station.objects.create(
            path_version=version,
            order=station_spec.order,
            slug=station_spec.slug,
            title=station_spec.title,
            role=station_spec.role,
        )
        Step.objects.bulk_create(
            Step(
                station=station,
                order=s.order,
                slug=s.slug,
                title=s.title,
                type=s.type,
                est_minutes=s.est_minutes,
                requires_laptop=s.requires_laptop,
                body_md=s.body_md,
                check_spec=s.check_spec,
            )
            for s in station_spec.steps
        )
    return version, True


# --- Enrollment -------------------------------------------------------------


def ordered_steps(path_version):
    return list(
        Step.objects.filter(station__path_version=path_version)
        .select_related("station")
        .order_by("station__order", "order")
    )


def get_active_enrollment(user):
    return (
        Enrollment.objects.filter(user=user, status=Enrollment.Status.ACTIVE)
        .select_related("path_version__path")
        .first()
    )


def enroll(user, path_version, pace=""):
    """
    Enroll a user, or return their existing active enrollment.

    Returns ``(enrollment, created)``. Safe against double submits.
    """
    existing = get_active_enrollment(user)
    if existing:
        return existing, False
    if not path_version.is_published:
        raise ProgressError("This path isn't published yet.", "path_unpublished")

    try:
        with transaction.atomic():
            enrollment = Enrollment.objects.create(user=user, path_version=path_version, pace=pace)
            steps = ordered_steps(path_version)
            StepProgress.objects.bulk_create(
                StepProgress(
                    enrollment=enrollment,
                    step=step,
                    status=StepProgress.Status.AVAILABLE
                    if index == 0
                    else StepProgress.Status.LOCKED,
                )
                for index, step in enumerate(steps)
            )
    except IntegrityError:
        # A concurrent request enrolled first; the constraint kept it to one.
        return get_active_enrollment(user), False
    return enrollment, True


def next_progress(enrollment):
    """The step a builder should do next: in progress first, then available."""
    progress = enrollment.progress.select_related("step__station")
    return (
        progress.filter(status=StepProgress.Status.IN_PROGRESS).first()
        or progress.filter(status=StepProgress.Status.AVAILABLE).first()
    )


def get_progress(enrollment, step_slug):
    return enrollment.progress.select_related("step__station").filter(step__slug=step_slug).first()


# --- Transitions --------------------------------------------------------------


def start_step(progress):
    if progress.status == StepProgress.Status.LOCKED:
        raise ProgressError("Finish the previous step first.", "step_locked")
    if progress.status == StepProgress.Status.AVAILABLE:
        progress.status = StepProgress.Status.IN_PROGRESS
        progress.started_at = timezone.now()
        progress.save(update_fields=["status", "started_at", "updated"])
    return progress


@transaction.atomic
def complete_step(progress, verified=False):
    """
    Mark a step done and unlock the next one. Idempotent for finished steps.

    ``verified`` must be True for steps with a check: only a passing CheckRun
    may complete them.
    """
    progress = StepProgress.objects.select_for_update().select_related("step").get(pk=progress.pk)
    if progress.is_finished:
        return progress
    if progress.status == StepProgress.Status.LOCKED:
        raise ProgressError("Finish the previous step first.", "step_locked")
    if progress.step.has_check and not verified:
        raise ProgressError(
            "This step is completed by passing its check. Run 'Check my work'.",
            "check_required",
        )

    now = timezone.now()
    progress.status = StepProgress.Status.DONE
    progress.started_at = progress.started_at or now
    progress.completed_at = now
    progress.save(update_fields=["status", "started_at", "completed_at", "updated"])
    _unlock_next(progress)
    return progress


def _unlock_next(progress):
    following = (
        StepProgress.objects.filter(
            enrollment=progress.enrollment, status=StepProgress.Status.LOCKED
        )
        .select_related("step__station")
        .order_by("step__station__order", "step__order")
        .first()
    )
    if following:
        following.status = StepProgress.Status.AVAILABLE
        following.save(update_fields=["status", "updated"])
