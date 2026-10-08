from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class OnboardingDraft(TimeStampedModel):
    """
    Onboarding answers saved as the builder goes, so a refresh, another device
    or an expired session never loses them. Deleted when onboarding completes.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="onboarding_draft"
    )
    data = models.JSONField(default=dict)
    step = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return f"{self.user_id} at step {self.step}"
