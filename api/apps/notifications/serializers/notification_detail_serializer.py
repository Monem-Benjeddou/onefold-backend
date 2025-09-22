"""
Notification Detail Serializer

Detailed serializer for individual notification views with update capabilities.
Handles status updates with proper timestamp management.
"""

from django.utils import timezone
from rest_framework import serializers

from ..models import Notification


class NotificationDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual notification views.

    Provides full notification details with controlled update capabilities.
    Only allows updating the status field with proper timestamp handling.
    """

    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "title",
            "body",
            "status",
            "created",
            "updated",
        ]
        read_only_fields = [
            "id",
            "user",
            "title",
            "body",
            "created",
            "updated",
        ]

    def update(self, instance, validated_data):
        """
        Only allow updating status field with proper timestamp handling.

        Automatically manages read_at timestamp based on status changes:
        - Sets read_at when status changes to MARKED_READ
        - Clears read_at when status changes to MARKED_UNREAD
        """

        if "status" in validated_data:
            instance.status = validated_data["status"]
            if validated_data["status"] == Notification.MARKED_READ:
                instance.read_at = timezone.now()
            elif validated_data["status"] == Notification.MARKED_UNREAD:
                instance.read_at = None
            instance.save()
        return instance
