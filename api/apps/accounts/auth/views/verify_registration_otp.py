import logging
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.auth.serializers.login_otp import RegistrationOTPVerifySerializer
from apps.accounts.user.serializers import UserSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class VerifyRegistrationOTPView(APIView):
    """
    API View for verifying OTP for registration.
    Activates the user account after successful OTP verification.
    """

    permission_classes = (AllowAny,)
    serializer_class = RegistrationOTPVerifySerializer

    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=300)
    @extend_schema(
        tags=["auth"],
        request=RegistrationOTPVerifySerializer,
        responses={
            200: {"description": _("Registration verification successful.")},
            400: {"description": _("Invalid OTP.")},
            404: {"description": _("User not found.")},
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Process registration OTP verification.
        Activates user account and returns user data and auth tokens if OTP is valid.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data.get("user")
        otp = serializer.validated_data.get("otp")

        if not user:
            raise serializers.ValidationError(
                {"error": [_("User could not be found.")]}
            )

        from apps.accounts.auth.models import OTP

        try:
            registration_otp = OTP.objects.get(
                user=user, code=otp, purpose="registration", is_used=False
            )
        except OTP.DoesNotExist:
            raise serializers.ValidationError(
                {"otp": [_("Invalid or expired registration OTP.")]}
            )

        if not registration_otp.is_valid():
            raise serializers.ValidationError(
                {"otp": [_("OTP has expired. Please request a new verification code.")]}
            )

        try:
            from django.db import transaction
            from apps.accounts.auth.services.otp_delivery_service import (
                OTPDeliveryService,
            )

            verification_updates = {
                "is_active": True,
                "is_email_verified": True,
                "is_phone_verified": True,
                "is_verified": True,
            }

            with transaction.atomic():
                registration_otp.mark_as_used()

                for field, value in verification_updates.items():
                    setattr(user, field, value)

                update_fields = list(verification_updates.keys()) + ["updated"]
                user.save(update_fields=update_fields)

            logger.info(
                f"User {user.email} account activated via OTP verification. Updated fields: {list(verification_updates.keys())}"
            )
        except Exception as e:
            logger.error(f"Failed to activate user account for {user.email}: {str(e)}")
            raise serializers.ValidationError(
                {"error": [_("Failed to activate account. Please try again.")]}
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": _("Account verified and activated successfully."),
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )
