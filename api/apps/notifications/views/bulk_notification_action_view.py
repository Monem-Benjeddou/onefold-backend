"""
Bulk Notification Action View

Function-based view for performing bulk actions on notifications.
Supports mark_read, mark_unread, delete, and snooze operations.
"""

from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from ..models import Notification
from ..serializers import BulkNotificationActionSerializer


@extend_schema(
    tags=["notifications"],
    summary="Perform bulk actions on notifications",
    description="""
    Perform bulk actions on multiple notifications at once.

    **Supported Actions**:
    - `mark_read`: Mark notifications as read
    - `mark_unread`: Mark notifications as unread
    - `delete`: Permanently delete notifications
    - `snooze`: Snooze notifications until specified time

    **Features**:
    - Process multiple notifications in a single request
    - User can only perform actions on their own notifications
    - Atomic operations with proper error handling
    - Authentication required

    **Request Body Example**:
    ```json
    {
        "action": "mark_read",
        "notification_ids": [1, 2, 3],
        "snooze_until": "2023-12-31T23:59:59Z"
    }
    ```

    **Response Example**:
    ```json
    {
        "success": true,
        "action": "mark_read",
        "count": 3
    }
    ```

    **Note**: `snooze_until` is required only for the `snooze` action.
    """,
    request=BulkNotificationActionSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the action was successful",
                },
                "action": {
                    "type": "string",
                    "description": "The action that was performed",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of notifications affected",
                },
            },
        },
        400: OpenApiTypes.OBJECT,
        401: OpenApiTypes.OBJECT,
    },
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def bulk_notification_action(request):
    """
    Perform bulk actions on notifications.

    Supported actions:
    - mark_read: Mark notifications as read
    - mark_unread: Mark notifications as unread
    - delete: Delete notifications
    - snooze: Snooze notifications until specified time

    Request body:
    {
        "action": "mark_read|mark_unread|delete|snooze",
        "notification_ids": [1, 2, 3],
        "snooze_until": "2023-12-31T23:59:59Z"  # Required for snooze action
    }

    Returns:
    {
        "success": true,
        "action": "mark_read",
        "count": 3
    }
    """
    serializer = BulkNotificationActionSerializer(data=request.data)
    if serializer.is_valid():
        action = serializer.validated_data["action"]
        notification_ids = serializer.validated_data["notification_ids"]

        notifications = Notification.objects.filter(
            id__in=notification_ids, user=request.user
        )

        if action == "mark_read":
            count = notifications.update(
                status=Notification.MARKED_READ, read_at=timezone.now()
            )
        elif action == "mark_unread":
            count = notifications.update(
                status=Notification.MARKED_UNREAD, read_at=None
            )
        elif action == "delete":
            count = notifications.count()
            notifications.delete()
        elif action == "snooze":
            snooze_until = serializer.validated_data["snooze_until"]
            count = notifications.update(
                status=Notification.SNOOZED, snooze_until=snooze_until
            )

        return Response({"success": True, "action": action, "count": count})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
