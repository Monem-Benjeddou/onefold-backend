"""Onboarding: one transaction from answers to an enrolled builder with a project."""

from django.db import transaction

from apps.learning import services as learning
from apps.projects.models import Project
from apps.projects.serializers import unique_project_slug

from .models import OnboardingDraft


def get_project(user):
    """The builder's current project (one per builder in the MVP)."""
    return Project.objects.filter(user=user).order_by("-created").first()


def is_onboarded(user):
    """Onboarded = an active enrollment and a project. Anything less goes back to onboarding."""
    if not user or not user.is_authenticated:
        return False
    return (
        learning.get_active_enrollment(user) is not None
        and Project.objects.filter(user=user).exists()
    )


def save_draft(user, data, step):
    draft, _ = OnboardingDraft.objects.update_or_create(
        user=user, defaults={"data": data, "step": step}
    )
    return draft


@transaction.atomic
def complete_onboarding(user, *, pace, experience, project_name, project_idea, idea=""):
    """
    Enroll the builder and create their project, all or nothing. Calling it
    again returns the same enrollment and project (safe to retry).

    Returns ``(enrollment, project, created)``.
    """
    version = learning.current_published_version()
    if version is None:
        raise learning.ProgressError("No path is published yet.", "path_unpublished")
    enrollment, enrolled_now = learning.enroll(user, version, pace=pace)
    enrollment.pace = pace
    enrollment.experience = experience
    enrollment.save(update_fields=["pace", "experience", "updated"])

    project = get_project(user)
    created = project is None
    if created:
        name = project_name.strip()
        project = Project.objects.create(
            user=user,
            enrollment=enrollment,
            name=name,
            slug=unique_project_slug(user, name),
            idea=(project_idea or idea).strip()[:280],
        )
    elif project.enrollment_id is None:
        project.enrollment = enrollment
        project.save(update_fields=["enrollment", "updated"])

    OnboardingDraft.objects.filter(user=user).delete()
    return enrollment, project, created or enrolled_now
