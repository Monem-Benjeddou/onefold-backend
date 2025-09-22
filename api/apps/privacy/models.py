from django.db import models

from core.abstract.models import AbstractAutoIncrementModel


class PrivacyPolicyPoint(AbstractAutoIncrementModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title
