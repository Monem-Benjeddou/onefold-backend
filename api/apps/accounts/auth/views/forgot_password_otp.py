from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.utils.translation import gettext_lazy as _
import logging

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.auth.serializers.forgot_password_otp import (
    ForgotPasswordOTPSerializer,
)

logger = logging.getLogger(__name__)


class ForgotPasswordOTPView(APIView):
    """
    API view for requesting password reset OTP.

    This view allows users to request a password reset OTP by providing their email address.
    An OTP will be generated and sent to the user's email for password reset verification.
    """

    serializer_class = ForgotPasswordOTPSerializer

    @extend_schema(
        tags=["auth"],
        summary="Request Password Reset OTP",
        description="Send a 6-digit OTP to the user's email for password reset verification.",
        request=ForgotPasswordOTPSerializer,
        responses={
            200: OpenApiResponse(
                description="Password reset OTP sent successfully",
                examples={
                    "application/json": {
                        "message": "Password reset OTP has been sent to your email."
                    }
                },
            ),
            400: OpenApiResponse(
                description="Bad request - invalid email or user not found",
                examples={
                    "application/json": {
                        "email": ["User with this email does not exist."]
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
        Request password reset OTP.

        Args:
            request: HTTP request containing email address

        Returns:
            Response with success message or error details
        """
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"Invalid password reset OTP request: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = serializer.save()
            logger.info(
                f"Password reset OTP requested for email: {serializer.validated_data['email']}"
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to process password reset OTP request: {str(e)}")
            return Response(
                {"error": [_("Failed to send password reset OTP. Please try again.")]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
