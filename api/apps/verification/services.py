import logging
import time
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.learning import services as learning
from apps.learning.models import StepProgress

from .executors import get_executor
from .models import CheckRun

logger = logging.getLogger(__name__)


class CheckRequestError(Exception):
    def __init__(self, message, code, status=409):
        super().__init__(message)
        self.code = code
        self.status = status


def request_check(project, step_slug, idempotency_key=""):
    """
    Validate a "Check my work" request and queue a CheckRun.

    Returns ``(check_run, created)``; a repeated idempotency key returns the
    original run instead of starting another.
    """
    if idempotency_key:
        existing = CheckRun.objects.filter(project=project, idempotency_key=idempotency_key).first()
        if existing:
            return existing, False

    enrollment = learning.get_active_enrollment(project.user)
    progress = learning.get_progress(enrollment, step_slug) if enrollment else None
    if progress is None:
        raise CheckRequestError("No such step in your path.", "step_not_found", status=404)
    step = progress.step
    if not step.has_check:
        raise CheckRequestError("This step has no check. Mark it done instead.", "no_check")
    if progress.status == StepProgress.Status.LOCKED:
        raise CheckRequestError("Finish the previous step first.", "step_locked")

    executor = get_executor(step.check_spec.get("kind"))
    if executor is None:
        raise CheckRequestError(
            "This check isn't available right now. That's on us.", "check_unavailable", status=503
        )
    problems = executor.preflight(step.check_spec, project)
    if problems:
        raise CheckRequestError(" ".join(problems), "preflight_failed", status=400)

    window_start = timezone.now() - timedelta(minutes=1)
    recent = CheckRun.objects.filter(project__user=project.user, created__gte=window_start).count()
    if recent >= settings.VERIFICATION_CHECKS_PER_MINUTE:
        raise CheckRequestError(
            "That's a lot of checks in a minute. Give it a few seconds and retry.",
            "rate_limited",
            status=429,
        )

    try:
        with transaction.atomic():
            run = CheckRun.objects.create(
                project=project,
                step=step,
                kind=step.check_spec["kind"],
                spec=step.check_spec,
                idempotency_key=idempotency_key,
            )
    except IntegrityError:
        # The same key raced in from a double click.
        return CheckRun.objects.get(project=project, idempotency_key=idempotency_key), False

    if progress.status == StepProgress.Status.AVAILABLE:
        learning.start_step(progress)
    return run, True


def run_check(check_run_id):
    """Execute a queued CheckRun. Safe to call twice; only the first runs."""
    claimed = CheckRun.objects.filter(pk=check_run_id, status=CheckRun.Status.QUEUED).update(
        status=CheckRun.Status.RUNNING, started_at=timezone.now()
    )
    if not claimed:
        return CheckRun.objects.get(pk=check_run_id)

    run = CheckRun.objects.select_related("project__user", "step").get(pk=check_run_id)
    started = time.monotonic()
    try:
        outcome = get_executor(run.kind).run(run.spec, run.project)
        run.status = CheckRun.Status.PASSED if outcome.passed else CheckRun.Status.FAILED
        run.result = outcome.as_result()
    except Exception:
        logger.exception("Check %s crashed", run.pk)
        run.status = CheckRun.Status.ERROR
        run.result = {
            "passed": False,
            "checked": "",
            "got": {},
            "reasons": ["We couldn't run the check. That's on us, not you."],
            "hints": [f"Retry in a minute. If it keeps happening, quote check {run.pk}."],
        }
    run.duration_ms = int((time.monotonic() - started) * 1000)
    run.finished_at = timezone.now()
    run.save(update_fields=["status", "result", "duration_ms", "finished_at", "updated"])

    if run.status == CheckRun.Status.PASSED:
        _complete_step(run)
    return run


def _complete_step(run):
    enrollment = learning.get_active_enrollment(run.project.user)
    if enrollment is None:
        return
    progress = learning.get_progress(enrollment, run.step.slug)
    if progress and progress.step_id == run.step_id:
        learning.complete_step(progress, verified=True)
