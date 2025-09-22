from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from django.db import models
from django.apps import apps
from django.conf import settings

from apps.accounts.user.models import VerificationCode
from core.tasks import send_activation_email
from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService


User = get_user_model()
Country = apps.get_model("countries", "Country")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        max_length=128,
        error_messages={
            "min_length": _("Password must be at least 8 characters long."),
            "max_length": _("Password cannot exceed 128 characters."),
            "required": _("Password is required."),
        },
    )
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=15,
        error_messages={
            "max_length": _("Phone number cannot exceed 15 characters."),
        },
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "fullname",
            "password",
            "phone_number",
        ]

    def validate_email(self, value):
        """
        Check that the email doesn't exist already (case-insensitive).
        """
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("User with this email already exists."))

        return value.lower()

    def validate_phone_number(self, value):
        """
        Validate phone number format and uniqueness.
        """
        if value in (None, ""):
            return None

        phone_number = value.strip()
        if phone_number == "":
            return None

        import re

        if not re.match(r"^[\d\s\-\(\)\+]+$", phone_number):
            raise serializers.ValidationError(
                _("Phone number contains invalid characters.")
            )

        digits_only = "".join(filter(str.isdigit, phone_number))
        if len(digits_only) < 5:
            raise serializers.ValidationError(
                _("Phone number must contain at least 5 digits.")
            )

        if len(digits_only) > 15:
            raise serializers.ValidationError(
                _("Phone number cannot exceed 15 digits.")
            )

        if User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError(
                _("User with this phone number already exists.")
            )

        return phone_number

    def validate(self, data):
        """
        Additional cross-field validation.
        OTP is disabled; no phone/email OTP gating here.
        """
        return data

    def create(self, validated_data):
        validated_data["role"] = "collector"
        user = User.objects.create_user(**validated_data)
        # Mark email as verified since OTP is disabled
        try:
            if hasattr(user, "is_email_verified"):
                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"]) 
        except Exception:
            pass
        return user

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        try:
            rep["avatar"] = (
                self.context["request"].build_absolute_uri(instance.avatar.url)
                if instance.avatar
                else None
            )
        except (AttributeError, ValueError, KeyError):
            rep["avatar"] = None
        return rep


class EmailVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, min_length=6)
    email = serializers.EmailField()

    def validate_email(self, value):
        """Normalize email to lowercase and check if user exists"""
        email = value.lower()
        try:
            User.objects.get(email__iexact=email)
            return email
        except User.DoesNotExist:
            raise serializers.ValidationError(_("User does not exist"))

    def validate(self, data):
        code = data.get("code")
        email = data.get("email")

        try:
            user = User.objects.get(email__iexact=email)
            data["user"] = user

            from apps.accounts.auth.models import OTP

            try:
                otp = OTP.objects.get(
                    user=user, code=code, purpose="verification", is_used=False
                )
                if not otp.is_valid():
                    raise serializers.ValidationError(
                        {
                            "code": _(
                                "OTP has expired. Please request a new verification code."
                            )
                        }
                    )
                data["otp"] = otp
                data["verification_type"] = "otp"
                return data
            except OTP.DoesNotExist:

                try:
                    verification_code = VerificationCode.objects.get(
                        code=code, user=user
                    )
                    data["verification_code"] = verification_code
                    data["verification_type"] = "legacy"
                    return data
                except VerificationCode.DoesNotExist:
                    raise serializers.ValidationError(
                        {"code": _("Invalid verification code")}
                    )
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": _("User does not exist")})

    def create(self, validated_data):
        email = validated_data.get("email")
        code = validated_data.get("code")

        try:
            user = User.objects.get(email__iexact=email)
            verification_code = VerificationCode.objects.get(code=code, user=user)

            verification_code.delete()

            return {"email": email, "verified": True}
        except (User.DoesNotExist, VerificationCode.DoesNotExist):
            return validated_data


class ResendVerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False, max_length=15)

    def validate_email(self, value):
        """Normalize email to lowercase and check if user exists"""
        if value:
            email = value.lower()
            try:
                User.objects.get(email__iexact=email)
                return email
            except User.DoesNotExist:
                raise serializers.ValidationError(_("User does not exist."))
        return value

    def validate_phone_number(self, value):
        """Validate phone number format and check if user exists"""
        if value:
            phone_number = value.strip()
            if not phone_number:
                return None

            import re

            if not re.match(r"^[\d\s\-\(\)\+]+$", phone_number):
                raise serializers.ValidationError(
                    _("Phone number contains invalid characters.")
                )

            digits_only = "".join(filter(str.isdigit, phone_number))
            if len(digits_only) < 5:
                raise serializers.ValidationError(
                    _("Phone number must contain at least 5 digits.")
                )

            if len(digits_only) > 15:
                raise serializers.ValidationError(
                    _("Phone number cannot exceed 15 digits.")
                )

            try:
                User.objects.get(phone_number=phone_number)
                return phone_number
            except User.DoesNotExist:
                raise serializers.ValidationError(_("User does not exist."))
        return value

    def validate(self, data):
        """Ensure exactly one of email or phone_number is provided"""
        email = data.get("email")
        phone_number = data.get("phone_number")

        if not email and not phone_number:
            raise serializers.ValidationError(
                _("Either email or phone number must be provided.")
            )

        if email and phone_number:
            raise serializers.ValidationError(
                _("Please provide either email or phone number, not both.")
            )

        return data

    def create(self, validated_data):
        email = validated_data.get("email")
        phone_number = validated_data.get("phone_number")

        if email:
            user = User.objects.get(email__iexact=email)
        else:
            user = User.objects.get(phone_number=phone_number)

        if phone_number:

            if not user.phone_number:
                raise serializers.ValidationError(
                    {
                        "phone_number": _(
                            "User does not have a phone number for SMS verification."
                        )
                    }
                )

            otp_code = user.get_or_generate_verification_code("registration")

            otp_sent = OTPDeliveryService.send_sms_otp(user, otp_code, "registration")

            if not otp_sent:

                from apps.accounts.auth.models import OTP

                OTP.objects.filter(user=user, purpose="registration").delete()
                raise serializers.ValidationError(
                    {
                        "phone_number": _(
                            "Failed to send verification code via SMS. Please check your phone number and try again later."
                        )
                    }
                )

        else:

            if not user.email:
                raise serializers.ValidationError(
                    {
                        "email": _(
                            "User does not have an email address for email verification."
                        )
                    }
                )

            otp_code = user.get_or_generate_verification_code("registration")

            otp_sent = OTPDeliveryService.send_email_otp(user, otp_code, "registration")

            if not otp_sent:

                from apps.accounts.auth.models import OTP

                OTP.objects.filter(user=user, purpose="registration").delete()
                raise serializers.ValidationError(
                    {
                        "email": _(
                            "Failed to send verification code via email. Please try again later."
                        )
                    }
                )

        return user
