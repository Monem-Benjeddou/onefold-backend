from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

from core.tasks import send_activation_email

User = get_user_model()
logger = logging.getLogger(__name__)


class ResetPasswordOTPSerializer(serializers.Serializer):
    """
    Serializer for resetting password using OTP.
    """

    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6, min_length=6)
    new_password = serializers.CharField(
        style={"input_type": "password"}, required=True, write_only=True
    )
    confirm_password = serializers.CharField(
        style={"input_type": "password"}, required=True, write_only=True
    )

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

    def validate_otp(self, value):
        """
        Validate that OTP contains exactly 6 numeric digits.
        """
        if not value.isdigit():
            raise serializers.ValidationError(_("OTP must contain only numbers."))
        if len(value) != 6:
            raise serializers.ValidationError(_("OTP must be exactly 6 digits."))
        return value

    def validate_new_password(self, value):
        """
        Validate the new password using Django's password validators.
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """
        Validate that passwords match and OTP is valid.
        """
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")
        email = attrs.get("email")
        otp = attrs.get("otp")

        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": [_("Password confirmation does not match.")]}
            )

        if email and otp:
            user = User.objects.get(email__iexact=email)

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
                    raise serializers.ValidationError(
                        {"otp": [_("Invalid or expired OTP.")]}
                    )
            except Exception as e:
                logger.error(
                    f"Failed to verify password reset OTP for user {user.email}: {str(e)}"
                )
                raise serializers.ValidationError(
                    {"otp": [_("Invalid or expired OTP.")]}
                )

            if user.check_password(new_password):
                raise serializers.ValidationError(
                    {
                        "new_password": [
                            _(
                                "New password must be different from your current password."
                            )
                        ]
                    }
                )

        return attrs

    def save(self, **kwargs):
        """
        Reset the user's password and send confirmation email.
        """
        email = self.validated_data["email"]
        new_password = self.validated_data["new_password"]

        user = User.objects.get(email__iexact=email)

        try:
            from django.db import transaction
            from apps.accounts.auth.services.otp_delivery_service import (
                OTPDeliveryService,
            )

            with transaction.atomic():
                user.set_password(new_password)

                
                verification_updates = {}
                if not user.is_email_verified:
                    verification_updates["is_email_verified"] = True
                    user.is_email_verified = True

                
                update_fields = ["password"]
                if verification_updates:
                    update_fields.extend(verification_updates.keys())
                update_fields.append("updated")
                user.save(update_fields=update_fields)

            logger.info(
                f"Password reset successfully for user {user.email}. Verification updates: {list(verification_updates.keys()) if verification_updates else 'none'}"
            )

            text_content = _("Your password has been reset successfully.")
            html_content = render_to_string(
                "reset_password_confirmation_email.html", {"user": user}
            )

            send_activation_email.delay(
                _("Password Reset Confirmation"),
                text_content,
                user.email,
                html_content=html_content,
            )

        except Exception as e:
            logger.error(f"Failed to reset password for user {user.email}: {str(e)}")
            raise serializers.ValidationError(
                {"error": [_("Failed to reset password. Please try again.")]}
            )

        return {"message": _("Password has been reset successfully.")}
