"""
Notification Stats View

Function-based view for retrieving notification statistics.
Provides comprehensive stats about user's notifications.
"""

from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from ..models import Notification


@extend_schema(
    tags=["notifications"],
    summary="Get notification statistics",
    description="""
    Retrieve comprehensive notification statistics for the authenticated user.

    **Features**:
    - Total count of all notifications
    - Count of unread notifications
    - Count of read notifications
    - Count of snoozed notifications
    - Authentication required

    **Response Format**:
    ```json
    {
        "total": 25,
        "unread": 5,
        "read": 18,
        "snoozed": 2
    }
    ```

    **Use Cases**:
    - Dashboard notification counters
    - Badge counts for UI elements
    - Analytics and reporting
    """,
    responses={
        200: {
            "type": "object",
            "properties": {
                "total": {
                    "type": "integer",
                    "description": "Total number of notifications",
                },
                "unread": {
                    "type": "integer",
                    "description": "Number of unread notifications",
                },
                "read": {
                    "type": "integer",
                    "description": "Number of read notifications",
                },
                "snoozed": {
                    "type": "integer",
                    "description": "Number of snoozed notifications",
                },
            },
        },
        401: OpenApiTypes.OBJECT,
    },
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def notification_stats(request):
    """
    Get notification statistics for the authenticated user.

    Returns comprehensive statistics including:
    - total: Total number of notifications
    - unread: Number of unread notifications
    - read: Number of read notifications
    - snoozed: Number of snoozed notifications

    Response format:
    {
        "total": 25,
        "unread": 5,
        "read": 18,
        "snoozed": 2
    }
    """
    user_notifications = Notification.objects.filter(user=request.user)

    stats = {
        "total": user_notifications.count(),
        "unread": user_notifications.filter(status=Notification.MARKED_UNREAD).count(),
        "read": user_notifications.filter(status=Notification.MARKED_READ).count(),
        "snoozed": user_notifications.filter(status=Notification.SNOOZED).count(),
    }

    return Response(stats)
