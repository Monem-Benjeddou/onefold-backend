from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema

from apps.accounts.auth.serializers.register import ResendVerificationCodeSerializer
from apps.accounts.user.serializers import UserSerializer
from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService
from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit


class ResendVerificationCodeView(APIView):
    """
    API View for resending verification codes via SMS or email.

    Accepts either email or phone_number (exactly one required).
    The delivery method is determined by the field provided in the request:
    - If 'email' is provided: sends email verification code
    - If 'phone_number' is provided: sends SMS verification code
    """

    serializer_class = ResendVerificationCodeSerializer

    @extend_schema(
        tags=["auth"],
        request=ResendVerificationCodeSerializer,
        responses={200: {"message": _("Verification code sent successfully")}},
    )
    @api_error_handler
    @dynamic_rate_limit(default_rate=5, default_period=300)
    def post(self, request):
        """
        Resends the verification code to the user.

        Accepts either email or phone_number (exactly one required).
        The delivery method is determined by the field provided in the request:
        - If 'email' is provided: sends email verification code
        - If 'phone_number' is provided: sends SMS verification code
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        message = _("Verification code sent successfully")

        return Response(
            {"message": message},
            status=status.HTTP_200_OK,
        )
