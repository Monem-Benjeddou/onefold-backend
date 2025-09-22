"""
Admin View for User Banning

Admin-specific view for banning user accounts temporarily.
"""

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from datetime import datetime, timedelta

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.models import User
from apps.accounts.user.permissions import CanManageUsers
from apps.accounts.user.serializers.ban_user import (
    BanUserSerializer,
    BanUserResponseSerializer,
)


@extend_schema(tags=["Admin"])
class BanUserView(GenericAPIView):
    """
    Admin view for banning user accounts temporarily.

    This view allows administrators to ban user accounts with optional expiration.
    Only staff or superuser can ban users.
    Non-superusers cannot ban superuser accounts.
    Users cannot ban their own accounts.
    """

    queryset = User.objects.all()
    serializer_class = BanUserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=60)
    @extend_schema(
        description="""
        Ban a user account temporarily or permanently.

        Only staff or superuser can ban users. Non-superusers cannot ban superuser accounts.
        Users cannot ban their own accounts.

        Request body:
        - reason: Optional reason for banning the user (max 1000 characters)
        - duration_hours: Optional duration in hours (1-8760). If not provided, ban is permanent

        Response includes ban details with timestamps and expiration information.
        """,
        request=BanUserSerializer,
        responses={
            200: BanUserResponseSerializer,
            400: {
                "description": "Bad request",
                "examples": {
                    "already_banned": {
                        "summary": "User already banned",
                        "value": {"detail": "User is already banned."},
                    },
                    "self_ban": {
                        "summary": "Cannot ban own account",
                        "value": {"detail": "Cannot ban your own account."},
                    },
                    "invalid_duration": {
                        "summary": "Invalid duration",
                        "value": {"detail": "Duration must be a positive number."},
                    },
                },
            },
            403: {
                "description": "Permission denied",
                "examples": {
                    "superuser_ban": {
                        "summary": "Cannot ban superuser",
                        "value": {
                            "detail": "Permission denied. Cannot ban superuser accounts."
                        },
                    },
                    "insufficient_permissions": {
                        "summary": "Insufficient permissions",
                        "value": {
                            "detail": "Permission denied. Only staff or superuser can ban users."
                        },
                    },
                },
            },
            404: {"description": "User not found"},
        },
        tags=["User Management", "Admin"],
        summary="Ban a user account",
        operation_id="ban_user",
    )
    def patch(self, request, pk=None):
        """Ban a user account"""
        return self._ban_user(request)

    def put(self, request, pk=None):
        """Ban a user account"""
        return self._ban_user(request)

    def _ban_user(self, request):
        """Internal method to handle ban logic"""
        user = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {
                    "detail": _(
                        "Permission denied. Only staff or superuser can ban users."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.is_superuser and not request.user.is_superuser:
            return Response(
                {"detail": _("Permission denied. Cannot ban superuser accounts.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user == request.user:
            return Response(
                {"detail": _("Cannot ban your own account.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_currently_banned():
            return Response(
                {"detail": _("User is already banned.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = validated_data.get("reason", "")
        duration_hours = validated_data.get("duration_hours")

        user.is_banned = True
        user.ban_reason = reason
        user.banned_at = timezone.now()
        user.banned_by = request.user

        if duration_hours:
            user.ban_expires_at = timezone.now() + timedelta(hours=duration_hours)
        else:
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

        response_data = {
            "detail": _("User banned successfully"),
            "user_id": str(user.id),
            "is_banned": user.is_banned,
            "ban_reason": user.ban_reason,
            "banned_at": user.banned_at.isoformat() if user.banned_at else None,
            "banned_by": str(user.banned_by.id) if user.banned_by else None,
            "ban_expires_at": (
                user.ban_expires_at.isoformat() if user.ban_expires_at else None
            ),
            "is_permanent": user.ban_expires_at is None,
            "updated_at": (
                user.updated.isoformat() if hasattr(user, "updated") else None
            ),
        }

        return Response(response_data, status=status.HTTP_200_OK)

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
