from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.contrib.auth import get_user_model
import logging

from core.tasks import send_activation_email
from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService

User = get_user_model()
logger = logging.getLogger(__name__)


class ForgotPasswordOTPSerializer(serializers.Serializer):
    """
    Serializer for requesting an OTP for password reset.
    """

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """
        Validate that the email corresponds to an existing user.
        """
        email = value.lower()
        try:
            User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("User with this email does not exist."))
        return email

    def save(self, **kwargs):
        """
        Generate OTP and send password reset email.
        """
        email = self.validated_data["email"]
        user = User.objects.get(email__iexact=email)

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
            code = user.generate_verification_code("password_reset")
            logger.info(
                f"Generated password reset OTP for user {user.email}: {len(code)} characters"
            )
        except Exception as e:
            logger.error(
                f"Failed to generate password reset OTP for user {user.email}: {str(e)}"
            )
            raise serializers.ValidationError(
                {"error": [_("Failed to generate OTP. Please try again.")]}
            )

        try:
            otp_sent = user.send_otp(otp_type="password_reset")
            if not otp_sent:
                logger.warning(
                    f"Failed to send password reset OTP to user {user.email}"
                )
                raise serializers.ValidationError(
                    {
                        "error": [
                            _("Failed to send password reset OTP. Please try again.")
                        ]
                    }
                )
        except Exception as e:
            logger.error(
                f"Failed to send password reset OTP to user {user.email}: {str(e)}"
            )
            raise serializers.ValidationError(
                {"error": [_("Failed to send password reset OTP. Please try again.")]}
            )

        delivery_target = OTPDeliveryService.get_delivery_target_display(user)

        return {
            "message": _("Password reset OTP has been sent to {}").format(
                delivery_target
            )
        }
