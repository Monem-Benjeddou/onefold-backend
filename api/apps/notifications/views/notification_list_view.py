"""
Notification List View

Generic list view for user notifications with filtering and pagination.
Follows Django/DRF best practices with clean separation of concerns.
"""

from datetime import datetime

from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from ..models import Notification
from ..serializers import NotificationSerializer
from core.abstract.paginations import MetaPageNumberPagination


@extend_schema(
    tags=["notifications"],
    summary="List user notifications",
    description="""
    Retrieve a paginated list of notifications for the authenticated user with comprehensive filtering options.

    **Features**:
    - Filtering by status (all, read, unread, or specific status)
    - Filtering by notification type
    - Filtering by priority level
    - Filtering by creation date (since parameter)
    - Paginated responses with metadata
    - Ordered by creation date (newest first)
    - Authentication required

    **Default Behavior**: Returns unread notifications if no status filter is specified.
    """,
    parameters=[
        OpenApiParameter(
            name="status",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by notification status (all, read, unread, or specific status)",
            default="unread",
        ),
        OpenApiParameter(
            name="type",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by notification type",
        ),
        OpenApiParameter(
            name="priority",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by priority level",
        ),
        OpenApiParameter(
            name="since",
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            description="Filter notifications created after this ISO datetime",
        ),
        OpenApiParameter(
            name="limit",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Number of results per page",
            default=5,
        ),
        OpenApiParameter(
            name="page",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Page number",
            default=1,
        ),
    ],
    responses={200: NotificationSerializer(many=True), 401: OpenApiTypes.OBJECT},
)
class NotificationListView(generics.ListAPIView):
    """
    List user notifications with filtering and pagination.

    Supports filtering by:
    - status: all, read, unread, or specific status
    - type: notification_type filter
    - priority: priority level filter
    - since: ISO datetime for filtering by creation date

    Returns paginated results with comprehensive metadata.
    """

    serializer_class = NotificationSerializer
    pagination_class = MetaPageNumberPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Get filtered queryset based on request parameters.

        Returns notifications for the authenticated user with applied filters.
        """
        queryset = Notification.objects.filter(user=self.request.user)

        status_filter = self.request.query_params.get("status", "unread")
        if status_filter == "all":

            pass
        elif status_filter == "read":
            queryset = queryset.filter(status=Notification.MARKED_READ)
        elif status_filter == "unread":
            queryset = queryset.filter(status=Notification.MARKED_UNREAD)
        elif status_filter:

            queryset = queryset.filter(status=status_filter)

        type_filter = self.request.query_params.get("type")
        if type_filter:
            queryset = queryset.filter(notification_type=type_filter)

        priority_filter = self.request.query_params.get("priority")
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)

        since = self.request.query_params.get("since")
        if since:
            try:
                since_date = datetime.fromisoformat(since.replace("Z", "+00:00"))
                queryset = queryset.filter(created__gte=since_date)
            except ValueError:

                pass

        return queryset.order_by("-created")
