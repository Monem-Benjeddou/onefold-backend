from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class IsValidOTPSerializer(serializers.Serializer):
    """
    Serializer for checking if an OTP is valid without consuming it.
    This endpoint validates the OTP but does not change any state.
    Supports both email and phone number lookup.
    """

    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False, max_length=15)
    otp = serializers.CharField(required=True, max_length=6, min_length=6)

    def validate_email(self, value):
        """
        Validate that the email corresponds to an existing user.
        """
        if not value:
            return value

        email = value.lower()
        try:
            User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("User with this email does not exist."))
        return email

    def validate_phone_number(self, value):
        """
        Validate that the phone number corresponds to an existing user.
        """
        if not value:
            return value

        try:
            User.objects.get(phone_number=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                _("User with this phone number does not exist.")
            )
        return value

    def validate_otp(self, value):
        """
        Validate that OTP contains exactly 6 numeric digits.
        """
        if not value.isdigit():
            raise serializers.ValidationError(_("OTP must contain only numbers."))
        if len(value) != 6:
            raise serializers.ValidationError(_("OTP must be exactly 6 digits."))
        return value

    def validate(self, attrs):
        """
        Validate that the OTP is valid for the given email or phone number without consuming it.
        """
        email = attrs.get("email")
        phone_number = attrs.get("phone_number")
        otp = attrs.get("otp")

        if not email and not phone_number:
            raise serializers.ValidationError(
                {"non_field_errors": [_("Either email or phone number is required.")]}
            )

        if not otp:
            return attrs

        user = None
        try:
            if email:
                user = User.objects.get(email__iexact=email)
            elif phone_number:
                user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            identifier = email or phone_number
            field_name = "email" if email else "phone_number"
            raise serializers.ValidationError(
                {
                    field_name: [
                        _("User with this {} does not exist.").format(
                            field_name.replace("_", " ")
                        )
                    ]
                }
            )

        if user:
            if not hasattr(user, "is_otp_valid"):
                logger.error(f"User model missing is_otp_valid method. User: {user}")
                raise serializers.ValidationError(
                    {
                        "error": [
                            _(
                                "OTP validation functionality not available. Please contact support."
                            )
                        ]
                    }
                )

            from apps.accounts.auth.models import OTP as OTPModel
            from django.utils import timezone

            try:
                otp_obj = OTPModel.objects.get(user=user, code=otp)
                if timezone.now() >= otp_obj.expires_at:
                    raise serializers.ValidationError(
                        {"otp": [_("Invalid or expired OTP.")]}
                    )
            except OTPModel.DoesNotExist:
                raise serializers.ValidationError(
                    {"otp": [_("Invalid or expired OTP.")]}
                )
            except Exception as e:
                identifier = email or phone_number
                logger.error(f"Failed to validate OTP for user {identifier}: {str(e)}")
                raise serializers.ValidationError(
                    {"otp": [_("Invalid or expired OTP.")]}
                )

        return attrs

    def save(self, **kwargs):
        """
        Return validation result without changing any state.
        """
        email = self.validated_data.get("email")
        phone_number = self.validated_data.get("phone_number")
        otp = self.validated_data["otp"]

        try:

            user = None

            if email:
                user = User.objects.get(email__iexact=email)
            elif phone_number:
                user = User.objects.get(phone_number=phone_number)
            else:
                return {"is_valid": False, "message": _("No identifier provided.")}

            from apps.accounts.auth.models import OTP
            from django.utils import timezone

            try:
                otp_obj = OTP.objects.get(user=user, code=otp)

                expires_at = otp_obj.expires_at
                current_time = timezone.now()

                if isinstance(expires_at, str):

                    from dateutil import parser

                    expires_at = parser.parse(expires_at)

                is_valid = current_time < expires_at
            except OTP.DoesNotExist:
                is_valid = False

            identifier = email or phone_number
            logger.info(
                f"OTP validation check for user {identifier}: {'valid' if is_valid else 'invalid'}"
            )

            return {
                "is_valid": is_valid,
                "message": (
                    _("OTP is valid.") if is_valid else _("OTP is invalid or expired.")
                ),
            }
        except Exception as e:
            identifier = email or phone_number
            logger.error(
                f"Failed to check OTP validity for user {identifier}: {str(e)}"
            )
            return {"is_valid": False, "message": _("OTP validation failed.")}
