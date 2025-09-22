from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.utils.translation import gettext_lazy as _
import logging

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.auth.serializers.is_valid_otp import IsValidOTPSerializer

logger = logging.getLogger(__name__)


class IsValidOTPView(APIView):
    """
    API view for checking if an OTP is valid without consuming it.

    This view allows validation of OTP codes without changing any state.
    The OTP remains valid and can be used for actual authentication later.
    """

    serializer_class = IsValidOTPSerializer

    @extend_schema(
        tags=["Authentication"],
        summary="Check OTP Validity",
        description="Validate if a 6-digit OTP is valid for the given email without consuming it. The OTP remains usable after this check.",
        request=IsValidOTPSerializer,
        responses={
            200: OpenApiResponse(
                description="OTP validation result",
                examples={
                    "application/json": {"is_valid": True, "message": "OTP is valid."}
                },
            ),
            400: OpenApiResponse(
                description="Bad request - invalid email, OTP format, or validation failed",
                examples={
                    "application/json": {
                        "email": ["User with this email does not exist."],
                        "otp": ["OTP must be exactly 6 digits."],
                    }
                },
            ),
            429: OpenApiResponse(description="Too many requests - rate limit exceeded"),
            500: OpenApiResponse(description="Internal server error"),
        },
    )
    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=300)
    def post(self, request):
        """
        Check if OTP is valid without consuming it.

        Args:
            request: HTTP request containing email and OTP

        Returns:
            Response with validation result and status message
        """
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"Invalid OTP validation request: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = serializer.save()

            email = serializer.validated_data.get("email", "unknown")
            is_valid = result.get("is_valid", False)
            logger.info(
                f"OTP validation check for {email}: {'valid' if is_valid else 'invalid'}"
            )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to process OTP validation request: {str(e)}")
            return Response(
                {
                    "is_valid": False,
                    "message": _("OTP validation failed. Please try again."),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
