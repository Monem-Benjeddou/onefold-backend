"""
Notification Detail View

Generic detail view for individual notification management.
Supports retrieve, update, and delete operations with proper permissions.
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema_view, extend_schema
from drf_spectacular.types import OpenApiTypes

from ..models import Notification
from ..serializers import NotificationSerializer


@extend_schema_view(
    get=extend_schema(
        tags=["notifications"],
        summary="Retrieve notification details",
        description="""
        Retrieve detailed information about a specific notification.

        **Features**:
        - Returns complete notification information
        - User can only access their own notifications
        - Proper permission validation with detailed error messages
        - Authentication required

        **Permissions**: Users can only retrieve their own notifications.
        """,
        responses={
            200: "NotificationDetailSerializer",
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    ),
    put=extend_schema(
        tags=["notifications"],
        summary="Update notification",
        description="""
        Update a notification (typically used for marking as read/unread).

        **Features**:
        - Update notification status and other fields
        - User can only update their own notifications
        - Partial updates supported
        - Authentication required

        **Common Use Cases**:
        - Mark notification as read/unread
        - Update notification priority
        - Snooze notifications

        **Permissions**: Users can only update their own notifications.
        """,
        responses={
            200: "NotificationDetailSerializer",
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    ),
    patch=extend_schema(
        tags=["notifications"],
        summary="Partially update notification",
        description="""
        Partially update a notification (typically used for marking as read/unread).

        **Features**:
        - Partial update of notification fields
        - User can only update their own notifications
        - Commonly used for status changes
        - Authentication required

        **Permissions**: Users can only update their own notifications.
        """,
        responses={
            200: "NotificationDetailSerializer",
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    ),
    delete=extend_schema(
        tags=["notifications"],
        summary="Delete notification",
        description="""
        Delete a specific notification.

        **Features**:
        - Permanently delete notification
        - User can only delete their own notifications
        - Authentication required

        **Permissions**: Users can only delete their own notifications.
        """,
        responses={
            204: None,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    ),
)
class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a notification.

    Provides full CRUD operations for individual notifications with:
    - Proper permission checking (user can only access their own notifications)
    - Detailed error handling for better UX
    - Uses NotificationDetailSerializer for detailed operations
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return notifications filtered by authenticated user."""
        return Notification.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use detailed serializer for individual notification operations."""
        from ..serializers import NotificationDetailSerializer

        return NotificationDetailSerializer

    def get_object(self):
        """
        Override to provide better permission error handling.

        Returns the notification object with proper permission validation.
        Raises PermissionDenied if user tries to access another user's notification.
        """
        pk = self.kwargs.get("pk")
        try:

            notification = get_object_or_404(Notification, pk=pk)

            if notification.user != self.request.user:
                raise PermissionDenied(
                    "You don't have permission to access this notification."
                )
            return notification
        except Notification.DoesNotExist:
            raise get_object_or_404(Notification, pk=pk)
