"""
View for user self-deactivation functionality.
"""

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.user.serializers import (
    SelfDeactivationRequestSerializer,
    SelfDeactivationResponseSerializer,
    AccountStatusSerializer,
)

User = get_user_model()


class IsActiveUser(BasePermission):
    """
    Custom permission to only allow active users to access the view.
    """

    message = _(
        "Your account is deactivated. Please contact support to reactivate your account."
    )

    def has_permission(self, request, view):
        """Check if the user is authenticated and active."""
        return request.user and request.user.is_authenticated and request.user.is_active


@extend_schema(tags=["User Account"])
class SelfDeactivationView(GenericAPIView):
    """
    View for users to deactivate their own accounts.

    This view allows authenticated users to deactivate their own accounts.
    Superusers are not allowed to self-deactivate for security reasons.
    """

    serializer_class = SelfDeactivationRequestSerializer
    permission_classes = [IsAuthenticated]

    @api_error_handler
    @dynamic_rate_limit(default_rate=3, default_period=300)
    @extend_schema(
        description="Deactivate your own account",
        request=SelfDeactivationRequestSerializer,
        responses={
            200: SelfDeactivationResponseSerializer,
            400: {"description": "Bad request"},
            403: {"description": "Permission denied"},
        },
    )
    def post(self, request):
        """Deactivate the authenticated user's account."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        reason = serializer.validated_data.get("reason", "")

        deactivated_user = User.objects.deactivate_user(user.id)

        if not deactivated_user:
            return Response(
                {
                    "detail": _(
                        "Failed to deactivate account. Account may already be deactivated."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_data = {
            "success": True,
            "message": _("Account deactivated successfully"),
            "deactivated_at": deactivated_user.deactivated_at,
            "user_id": str(user.id),
        }

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["User Account"])
class AccountStatusView(GenericAPIView):
    """
    View to get the current account status.

    Returns information about the user's account status including
    activation status, ban status, and relevant timestamps.
    """

    serializer_class = AccountStatusSerializer
    permission_classes = [IsAuthenticated]

    @api_error_handler
    @extend_schema(
        description="Get current account status",
        responses={
            200: AccountStatusSerializer,
        },
    )
    def get(self, request):
        """Get the current account status for the authenticated user."""
        user = request.user
        serializer = self.get_serializer(user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
