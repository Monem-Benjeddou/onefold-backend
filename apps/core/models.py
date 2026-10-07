import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """UUID primary key plus created/updated timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
