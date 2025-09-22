from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema

from core.decorators.error_handler import api_error_handler
from apps.accounts.auth.serializers.forgot_reset_password import (
    SetNewPasswordSerializer,
)
from core.ratelimiter import dynamic_rate_limit


class ResetPasswordView(APIView):
    """
    API View for resetting a user's password using a token.
    """

    serializer_class = SetNewPasswordSerializer
    permission_classes = (AllowAny,)

    @api_error_handler
    @dynamic_rate_limit(default_rate=5, default_period=3600)
    @extend_schema(
        tags=["auth"],
        request=SetNewPasswordSerializer,
        responses={
            200: {"description": _("Password reset successful.")},
            400: {"description": _("Invalid token or password.")},
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Process password reset request.
        Validates the token and sets a new password.
        """
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": _("Password has been reset successfully.")},
            status=status.HTTP_200_OK,
        )
