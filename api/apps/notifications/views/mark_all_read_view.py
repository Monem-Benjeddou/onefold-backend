"""
Mark All Read View

Function-based view for marking all notifications as read.
Provides bulk read operation for user convenience.
"""

from django.utils import timezone
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from ..models import Notification


@extend_schema(
    tags=["notifications"],
    summary="Mark all notifications as read",
    description="""
    Mark all unread notifications as read for the authenticated user.

    **Features**:
    - Bulk operation to mark all unread notifications as read
    - Sets read_at timestamp for all updated notifications
    - Returns count of notifications that were updated
    - Authentication required
    - Idempotent operation (safe to call multiple times)

    **Response Example**:
    ```json
    {
        "success": true,
        "message": "Marked 5 notifications as read",
        "count": 5,
        "updated_count": 5
    }
    ```

    **Use Cases**:
    - "Mark all as read" button functionality
    - Bulk notification management
    - Clearing notification badges
    """,
    request=None,
    responses={
        200: {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the operation was successful",
                },
                "message": {
                    "type": "string",
                    "description": "Human-readable success message",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of notifications marked as read",
                },
                "updated_count": {
                    "type": "integer",
                    "description": "Number of notifications actually updated",
                },
            },
        },
        401: OpenApiTypes.OBJECT,
    },
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_all_read(request):
    """
    Mark all notifications as read for the authenticated user.

    Updates all unread notifications to read status and sets read_at timestamp.

    Returns:
    {
        "success": true,
        "message": "Marked 5 notifications as read",
        "count": 5,
        "updated_count": 5
    }
    """
    notifications = Notification.objects.filter(
        user=request.user, status=Notification.MARKED_UNREAD
    )

    count = notifications.update(
        status=Notification.MARKED_READ, read_at=timezone.now()
    )

    return Response(
        {
            "success": True,
            "message": f"Marked {count} notifications as read",
            "count": count,
            "updated_count": count,
        }
    )
