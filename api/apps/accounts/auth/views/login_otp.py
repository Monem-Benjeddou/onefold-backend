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

from core.utilities import tprint
from core.decorators.error_handler import api_error_handler
from core.ratelimiter import dynamic_rate_limit
from apps.accounts.auth.serializers.login_otp import (
    OTPRequestSerializer,
    OTPVerifySerializer,
)
from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService

User = get_user_model()
logger = logging.getLogger(__name__)


class RequestOTPView(APIView):
    """
    API View for requesting OTP for login.
    """

    permission_classes = (AllowAny,)
    serializer_class = OTPRequestSerializer

    @api_error_handler
    @dynamic_rate_limit(default_rate=5, default_period=300)
    @extend_schema(
        tags=["auth"],
        request=OTPRequestSerializer,
        responses={
            200: {"description": _("OTP sent successfully.")},
            400: {"description": _("Invalid input data.")},
            404: {"description": _("User not found.")},
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Process OTP request.
        Sends OTP to the user's email.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data.get("user")
        if not user:
            raise serializers.ValidationError(
                {"error": [_("User could not be found.")]}
            )

        if not hasattr(user, "generate_verification_code"):
            logger.error(
                f"User model missing generate_verification_code method. User: {user}"
            )
            raise serializers.ValidationError(
                {
                    "error": [
                        _("OTP functionality not available. Please contact support.")
                    ]
                }
            )

        if not hasattr(user, "send_verification_email"):
            logger.error(
                f"User model missing send_verification_email method. User: {user}"
            )
            raise serializers.ValidationError(
                {
                    "error": [
                        _("Email functionality not available. Please contact support.")
                    ]
                }
            )

        is_valid, error_msg = OTPDeliveryService.validate_user_for_otp_delivery(user)
        if not is_valid:
            raise serializers.ValidationError({"error": [error_msg]})

        try:
            code = user.generate_verification_code()
            logger.info(f"Generated OTP for user {user.email}: {len(code)} characters")
        except Exception as e:
            logger.error(f"Failed to generate OTP for user {user.email}: {str(e)}")
            raise serializers.ValidationError(
                {"error": [_("Failed to generate OTP. Please try again.")]}
            )

        try:
            otp_sent = user.send_verification_email(email_type="otp")
            if not otp_sent:
                logger.warning(f"Failed to send OTP to user {user.email}")
                raise serializers.ValidationError(
                    {"error": [_("Failed to send OTP. Please try again.")]}
                )
        except Exception as e:
            logger.error(f"Failed to send OTP to user {user.email}: {str(e)}")
            raise serializers.ValidationError(
                {"error": [_("Failed to send OTP. Please try again.")]}
            )

        delivery_target = OTPDeliveryService.get_delivery_target_display(user)

        return Response(
            {"message": _("OTP sent to {}").format(delivery_target)},
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    """
    API View for verifying OTP for login.
    """

    permission_classes = (AllowAny,)
    serializer_class = OTPVerifySerializer

    @api_error_handler
    @dynamic_rate_limit(default_rate=10, default_period=300)
    @extend_schema(
        tags=["auth"],
        request=OTPVerifySerializer,
        responses={
            200: {"description": _("Login successful with OTP.")},
            400: {"description": _("Invalid OTP.")},
            404: {"description": _("User not found.")},
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Process OTP verification.
        Returns user data and auth tokens if OTP is valid.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data.get("user")
        otp = serializer.validated_data.get("otp")

        if not user:
            raise serializers.ValidationError(
                {"error": [_("User could not be found.")]}
            )

        if not hasattr(user, "verify_code"):
            logger.error(f"User model missing verify_code method. User: {user}")
            raise serializers.ValidationError(
                {
                    "error": [
                        _(
                            "OTP verification functionality not available. Please contact support."
                        )
                    ]
                }
            )

        try:
            is_valid = user.verify_code(otp)
            if not is_valid:
                raise serializers.ValidationError({"otp": [_("Invalid OTP.")]})
        except Exception as e:
            logger.error(f"Failed to verify OTP for user {user.email}: {str(e)}")
            raise serializers.ValidationError({"otp": [_("Invalid OTP.")]})

        
        try:
            from django.db import transaction
            from apps.accounts.auth.models import OTP

            
            recent_otp = (
                OTP.objects.filter(user=user, code=otp).order_by("-created_at").first()
            )

            if recent_otp:
                request_data = serializer.validated_data

                
                used_phone = request_data.get("phone_number") is not None
                used_email = request_data.get("email") is not None

                
                verification_updates = {
                    "is_email_verified": True,
                    "is_phone_verified": True,
                    "is_verified": True,
                    "is_active": True
                }
                
                otp_delivery_method = recent_otp.delivery_method
                
                if verification_updates:
                    with transaction.atomic():
                        for field, value in verification_updates.items():
                            setattr(user, field, value)

                        update_fields = list(verification_updates.keys()) + ["updated"]
                        user.save(update_fields=update_fields)

                    logger.info(
                        f"Updated verification status for user {user.email} (delivery: {otp_delivery_method}): {list(verification_updates.keys())}"
                    )

        except Exception as e:
            
            logger.error(
                f"Failed to update verification status for user {user.email}: {str(e)}"
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "fullname": user.fullname,
                },
            },
            status=status.HTTP_200_OK,
        )
