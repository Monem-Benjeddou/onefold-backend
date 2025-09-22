"""
Notification Serializer

Main serializer for notifications with delivery tracking and computed fields.
Provides comprehensive notification data with helper methods.
"""

from django.utils import timezone
from rest_framework import serializers

from ..models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications with delivery tracking.

    Includes computed fields for enhanced functionality:
    - content_object_type: Type of related content object
    - is_expired: Whether notification has expired
    - is_snoozed: Whether notification is currently snoozed
    - time_since_created: Human-readable time since creation
    """

    content_object_type = serializers.CharField(
        source="content_type.model", read_only=True
    )
    is_expired = serializers.SerializerMethodField()
    is_snoozed = serializers.SerializerMethodField()
    time_since_created = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "body",
            "status",
            "notification_type",
            "priority",
            "content_object_type",
            "object_id",
            "metadata",
            "action_url",
            "expires_at",
            "snooze_until",
            "delivered_at",
            "read_at",
            "clicked_at",
            "created",
            "updated",
            "is_expired",
            "is_snoozed",
            "time_since_created",
        ]
        read_only_fields = [
            "id",
            "delivered_at",
            "read_at",
            "clicked_at",
            "created",
            "updated",
            "is_expired",
            "is_snoozed",
            "time_since_created",
        ]

    def get_is_expired(self, obj):
        """Check if notification has expired."""
        return obj.is_expired()

    def get_is_snoozed(self, obj):
        """Check if notification is currently snoozed."""
        return obj.is_snoozed()

    def get_time_since_created(self, obj):
        """Get human-readable time since notification was created."""
        delta = timezone.now() - obj.created
        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "Just now"
