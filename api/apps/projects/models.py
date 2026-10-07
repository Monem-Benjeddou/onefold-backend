import secrets

from django.conf import settings
from django.db import models

from core.abstract.models import AbstractModel


def new_ownership_token():
    return f"onefold-verify-{secrets.token_urlsafe(16)}"


class Project(AbstractModel):
    """The product a builder is shipping while they follow a path."""

    class Visibility(models.TextChoices):
        UNLISTED = "unlisted", "Unlisted"
        PUBLIC = "public", "Public"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects"
    )
    enrollment = models.ForeignKey(
        "learning.Enrollment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80)
    idea = models.CharField(max_length=280, blank=True)
    repo_full_name = models.CharField(
        max_length=140, blank=True, help_text="GitHub 'owner/repo'"
    )
    live_url = models.URLField(max_length=300, blank=True)
    # Unlisted until the builder chooses otherwise at the ship moment.
    visibility = models.CharField(
        max_length=10, choices=Visibility.choices, default=Visibility.UNLISTED
    )
    # Exposed by the builder's app to prove they control `live_url`.
    ownership_token = models.CharField(max_length=64, default=new_ownership_token, editable=False)

    class Meta:
        ordering = ["-created"]
        constraints = [
            models.UniqueConstraint(fields=["user", "slug"], name="uniq_project_slug_per_user"),
        ]

    def __str__(self):
        return self.name
