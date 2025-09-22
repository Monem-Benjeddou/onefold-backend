from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class OTPRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting an OTP for login.
    Can accept either email or phone number based on OTP delivery method.
    """

    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False, max_length=15)

    def validate(self, data):
        """
        Validate that either email or phone number is provided and corresponds to an existing user.
        """
        from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService

        email = data.get("email")
        phone_number = data.get("phone_number")
        delivery_method = OTPDeliveryService.get_delivery_method()

        if not email and not phone_number:
            raise serializers.ValidationError(
                {"non_field_errors": [_("Either email or phone number is required.")]}
            )

        if delivery_method == "sms":
            if phone_number:
                try:
                    user = User.objects.get(phone_number=phone_number)
                    data["user"] = user
                    return data
                except User.DoesNotExist:
                    if email:

                        try:
                            user = User.objects.get(email__iexact=email.lower())
                            data["user"] = user
                            return data
                        except User.DoesNotExist:
                            pass
                    raise serializers.ValidationError(
                        {
                            "phone_number": [
                                _("User with this phone number does not exist.")
                            ]
                        }
                    )
            elif email:
                try:
                    user = User.objects.get(email__iexact=email.lower())
                    data["user"] = user
                    return data
                except User.DoesNotExist:
                    raise serializers.ValidationError(
                        {"email": [_("User with this email does not exist.")]}
                    )
        else:
            if email:
                try:
                    user = User.objects.get(email__iexact=email.lower())
                    data["user"] = user
                    return data
                except User.DoesNotExist:
                    raise serializers.ValidationError(
                        {"email": [_("User with this email does not exist.")]}
                    )
            else:
                raise serializers.ValidationError(
                    {"email": [_("Email is required for email-based OTP delivery.")]}
                )

        return data


class OTPVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying an OTP for login.
    Can accept either email or phone number based on OTP delivery method.
    """

    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False, max_length=15)
    otp = serializers.CharField(required=True)

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
        Validate that either email or phone number is provided and corresponds to an existing user.
        """
        from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService

        email = attrs.get("email")
        phone_number = attrs.get("phone_number")
        otp = attrs.get("otp")
        delivery_method = OTPDeliveryService.get_delivery_method()

        if not email and not phone_number:
            raise serializers.ValidationError(
                {"non_field_errors": [_("Either email or phone number is required.")]}
            )

        if not otp:
            return attrs

        if delivery_method == "sms":
            if phone_number:
                try:
                    user = User.objects.get(phone_number=phone_number)
                    attrs["user"] = user
                    return attrs
                except User.DoesNotExist:
                    if email:

                        try:
                            user = User.objects.get(email__iexact=email.lower())
                            attrs["user"] = user
                            return attrs
                        except User.DoesNotExist:
                            pass
                    raise serializers.ValidationError(
                        {
                            "phone_number": [
                                _("User with this phone number does not exist.")
                            ]
                        }
                    )
            elif email:
                try:
                    user = User.objects.get(email__iexact=email.lower())
                    attrs["user"] = user
                    return attrs
                except User.DoesNotExist:
                    raise serializers.ValidationError(
                        {"email": [_("User with this email does not exist.")]}
                    )
        else:
            if email:
                try:
                    user = User.objects.get(email__iexact=email.lower())
                    attrs["user"] = user
                    return attrs
                except User.DoesNotExist:
                    raise serializers.ValidationError(
                        {"email": [_("User with this email does not exist.")]}
                    )
            else:
                raise serializers.ValidationError(
                    {"email": [_("Email is required for email-based OTP delivery.")]}
                )

        return attrs


class RegistrationOTPVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying an OTP for registration.
    Can accept either email or phone number to identify the user,
    regardless of the delivery method used.
    """

    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False, max_length=15)
    otp = serializers.CharField(required=True)

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
        Validate that either email or phone number is provided and corresponds to an existing user.
        For registration OTP verification, we accept either field regardless of delivery method.
        """
        email = attrs.get("email")
        phone_number = attrs.get("phone_number")

        if not email and not phone_number:
            raise serializers.ValidationError(
                {"non_field_errors": [_("Either email or phone number is required.")]}
            )

        if email and phone_number:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("Please provide either email or phone number, not both.")
                    ]
                }
            )

        
        user = None

        if email:
            try:
                user = User.objects.get(email__iexact=email.lower())
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"email": [_("User with this email does not exist.")]}
                )
        elif phone_number:
            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"phone_number": [_("User with this phone number does not exist.")]}
                )

        if user:
            attrs["user"] = user

        return attrs
