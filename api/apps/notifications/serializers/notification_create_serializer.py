"""
Notification Create Serializer

Serializer for creating new notifications with validation.
Ensures required fields and proper data validation.
"""

from rest_framework import serializers

from ..models import Notification


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating notifications.

    Provides comprehensive validation for notification creation.
    Ensures all required fields are present and valid.
    """

    class Meta:
        model = Notification
        fields = [
            "user",
            "title",
            "body",
            "status",
            "notification_type",
            "priority",
            "metadata",
            "action_url",
            "expires_at",
        ]

    def validate(self, data):
        """
        Validate notification data.

        Ensures title and body are provided as they are essential
        for meaningful notifications.
        """
        if not data.get("title"):
            raise serializers.ValidationError("Title is required")
        if not data.get("body"):
            raise serializers.ValidationError("Body is required")
        return data
