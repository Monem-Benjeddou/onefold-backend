"""
Admin View for User Unbanning

Admin-specific view for unbanning user accounts.
"""

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.models import User
from apps.accounts.user.permissions import CanManageUsers
from apps.accounts.user.serializers.ban_user import UnbanUserResponseSerializer


@extend_schema(tags=["Admin"])
class UnbanUserView(GenericAPIView):
    """
    Admin view for unbanning user accounts.

    This view allows administrators to remove bans from user accounts.
    Only staff or superuser can unban users.
    Non-superusers cannot unban users that were banned by superusers.
    """

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=60)
    @extend_schema(
        description="""
        Remove ban from a user account.

        Only staff or superuser can unban users. Non-superusers cannot unban users
        that were banned by superusers.

        This endpoint clears all ban-related fields and allows the user to login again.
        """,
        responses={
            200: UnbanUserResponseSerializer,
            400: {
                "description": "Bad request",
                "examples": {
                    "not_banned": {
                        "summary": "User not banned",
                        "value": {"detail": "User is not banned."},
                    }
                },
            },
            403: {
                "description": "Permission denied",
                "examples": {
                    "superuser_ban": {
                        "summary": "Cannot unban user banned by superuser",
                        "value": {
                            "detail": "Permission denied. Cannot unban users banned by superusers."
                        },
                    },
                    "insufficient_permissions": {
                        "summary": "Insufficient permissions",
                        "value": {
                            "detail": "Permission denied. Only staff or superuser can unban users."
                        },
                    },
                },
            },
            404: {"description": "User not found"},
        },
        tags=["User Management", "Admin"],
        summary="Unban a user account",
        operation_id="unban_user",
    )
    def patch(self, request, pk=None):
        """Unban a user account"""
        return self._unban_user(request)

    def put(self, request, pk=None):
        """Unban a user account"""
        return self._unban_user(request)

    def _unban_user(self, request):
        """Internal method to handle unban logic"""
        user = self.get_object()

        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {
                    "detail": _(
                        "Permission denied. Only staff or superuser can unban users."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.is_banned:
            return Response(
                {"detail": _("User is not banned.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            user.banned_by
            and user.banned_by.is_superuser
            and not request.user.is_superuser
        ):
            return Response(
                {
                    "detail": _(
                        "Permission denied. Cannot unban users banned by superusers."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        user.is_banned = False
        user.ban_reason = None
        user.banned_at = None
        user.banned_by = None
        user.ban_expires_at = None

        user.save(
            update_fields=[
                "is_banned",
                "ban_reason",
                "banned_at",
                "banned_by",
                "ban_expires_at",
            ]
        )

        return Response(
            {
                "detail": _("User unbanned successfully"),
                "user_id": str(user.id),
                "is_banned": user.is_banned,
                "unbanned_at": timezone.now().isoformat(),
                "unbanned_by": str(request.user.id),
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
