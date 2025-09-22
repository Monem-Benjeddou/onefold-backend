"""
Notification List Serializer

Lightweight serializer for notification list views.
Provides essential fields for list display with minimal overhead.
"""

from rest_framework import serializers

from ..models import Notification


class NotificationListSerializer(serializers.ModelSerializer):
    """
    List serializer for notification list views.

    Provides essential notification fields for list display.
    Optimized for performance with minimal field set.
    Includes user context validation for security.
    """

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "body",
            "status",
            "created",
        ]
        read_only_fields = [
            "id",
            "title",
            "body",
            "status",
            "created",
        ]

    def validate(self, data):
        """
        Add user from request context if available.

        Ensures proper user association when creating notifications
        through list views (if applicable).
        """
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            data["user"] = request.user
        return data
