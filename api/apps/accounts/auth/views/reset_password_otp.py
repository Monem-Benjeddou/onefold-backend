from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.utils.translation import gettext_lazy as _
import logging

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.auth.serializers.reset_password_otp import ResetPasswordOTPSerializer

logger = logging.getLogger(__name__)


class ResetPasswordOTPView(APIView):
    """
    API view for resetting password using OTP.

    This view allows users to reset their password by providing their email,
    the OTP they received, and their new password.
    """

    serializer_class = ResetPasswordOTPSerializer

    @extend_schema(
        tags=["auth"],
        summary="Reset Password with OTP",
        description="Reset user password using the 6-digit OTP received via email.",
        request=ResetPasswordOTPSerializer,
        responses={
            200: OpenApiResponse(
                description="Password reset successfully",
                examples={
                    "application/json": {
                        "message": "Password has been reset successfully."
                    }
                },
            ),
            400: OpenApiResponse(
                description="Bad request - invalid data, OTP, or password validation failed",
                examples={
                    "application/json": {
                        "otp": ["Invalid or expired OTP."],
                        "new_password": ["This password is too common."],
                        "confirm_password": ["Password confirmation does not match."],
                    }
                },
            ),
            429: OpenApiResponse(description="Too many requests - rate limit exceeded"),
            500: OpenApiResponse(description="Internal server error"),
        },
    )
    @api_error_handler
    @dynamic_rate_limit(default_rate=5, default_period=300)
    def post(self, request):
        """
        Reset password using OTP.

        Args:
            request: HTTP request containing email, OTP, and new password

        Returns:
            Response with success message or error details
        """
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"Invalid password reset request: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = serializer.save()
            logger.info(
                f"Password reset successfully for email: {serializer.validated_data['email']}"
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to reset password: {str(e)}")
            return Response(
                {"error": [_("Failed to reset password. Please try again.")]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
