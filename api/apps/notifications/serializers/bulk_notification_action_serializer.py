"""
Bulk Notification Action Serializer

Serializer for bulk notification actions with comprehensive validation.
Supports mark_read, mark_unread, delete, and snooze operations.
"""

from rest_framework import serializers


class BulkNotificationActionSerializer(serializers.Serializer):
    """
    Serializer for bulk notification actions.

    Validates bulk operations on multiple notifications:
    - action: The operation to perform (mark_read, mark_unread, delete, snooze)
    - notification_ids: List of notification IDs to operate on
    - snooze_until: Required datetime for snooze operations
    """

    action = serializers.ChoiceField(
        choices=["mark_read", "mark_unread", "delete", "snooze"]
    )
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )
    snooze_until = serializers.DateTimeField(required=False)

    def validate(self, data):
        """
        Validate bulk action data.

        Ensures snooze_until is provided when action is snooze.
        """
        if data["action"] == "snooze" and not data.get("snooze_until"):
            raise serializers.ValidationError(
                "snooze_until is required when action is snooze"
            )
        return data
