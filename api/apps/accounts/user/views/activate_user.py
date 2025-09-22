"""
Admin View for User Activation

Admin-specific view for activating user accounts.
"""

from rest_framework import status
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.models import User
from apps.accounts.user.permissions import IsBusinessAdminOrNeoAdmin
from apps.accounts.user.serializers import UserSerializer


@extend_schema(tags=["Admin"])
class ActivateUserView(UpdateAPIView):
    """
    Admin view for activating user accounts.

    This view allows administrators to activate user accounts.
    Non-superusers cannot activate superuser accounts.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsBusinessAdminOrNeoAdmin]
    lookup_field = "pk"

    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=60)
    @extend_schema(
        description="Activate a user account",
        responses={
            200: {"description": "User activated successfully"},
            404: {"description": "User not found"},
            403: {"description": "Permission denied"},
        },
    )
    def patch(self, request, *args, **kwargs):
        """Activate a user account"""
        user = self.get_object()

        if user.is_superuser and not request.user.is_superuser:
            return Response(
                {"detail": _("Permission denied. Cannot activate superuser accounts.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        user.is_active = True
        user.save(update_fields=["is_active"])

        return Response(
            {
                "detail": _("User activated successfully"),
                "user_id": str(user.id),
                "is_active": user.is_active,
                "updated_at": (
                    user.updated.isoformat() if hasattr(user, "updated") else None
                ),
            },
            status=status.HTTP_200_OK,
        )

    def get_object(self):
        """
        Override get_object to ensure proper error handling
        """
        try:
            return super().get_object()
        except User.DoesNotExist:
            return Response(
                {"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND
            )
