import json

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from core.abstract.models import AbstractModelTimeStamp
from django.conf import settings

User = get_user_model()


class Notification(AbstractModelTimeStamp):
    MARKED_READ = "r"
    MARKED_UNREAD = "u"
    SNOOZED = "s"

    STATUS_CHOICES = (
        (MARKED_READ, "read"),
        (MARKED_UNREAD, "unread"),
        (SNOOZED, "snoozed"),
    )

    CHOICES = STATUS_CHOICES

    NOTIFICATION_TYPES = (
        ("mention", "Mention"),
        ("reply", "Reply"),
        ("reaction", "Reaction"),
        ("follow", "Follow"),
        ("message", "Direct Message"),
        ("system", "System"),
        ("moderation", "Moderation"),
        ("achievement", "Achievement"),
        ("event", "Event"),
        ("live_update", "Live Update"),
    )

    PRIORITY_CHOICES = (
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="notifications",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=250, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    status = models.CharField(
        choices=STATUS_CHOICES, default=MARKED_UNREAD, max_length=1
    )
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES, default="system"
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="normal"
    )

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    metadata = models.JSONField(default=dict, blank=True)
    action_url = models.URLField(blank=True, null=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    snooze_until = models.DateTimeField(null=True, blank=True)

    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["notification_type", "created"]),
            models.Index(fields=["priority", "created"]),
        ]

    def mark_as_read(self):
        self.status = self.MARKED_READ
        self.read_at = timezone.now()
        self.save(update_fields=["status", "read_at"])

    def mark_as_delivered(self):
        if not self.delivered_at:
            self.delivered_at = timezone.now()
            self.save(update_fields=["delivered_at"])

    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at

    def is_snoozed(self):
        return self.snooze_until and timezone.now() < self.snooze_until
