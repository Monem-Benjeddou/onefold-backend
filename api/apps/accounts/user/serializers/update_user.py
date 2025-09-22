from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import IntegrityError

from core.abstract.serializers import AbstractSerializer
from apps.accounts.user.models import User


class UpdateUserSerializer(AbstractSerializer):
    bio = serializers.CharField(required=False, allow_blank=True)
    avatar = serializers.ImageField(required=False)
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
        max_length=15,
    )
    fullname = serializers.CharField(required=False, allow_blank=True)
    is_verified = serializers.BooleanField(required=False)
    country_name = serializers.SerializerMethodField()
    role_translated = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "avatar",
            "fullname",
            "phone_number",
            "country",
            "country_name",
            "role",
            "role_translated",
            "bio",
            "is_verified",
        ]
        read_only_fields = [
            "id",
            "country_name",
            "role_translated",
        ]

    def get_country_name(self, obj):
        """Get the country name from the related country object"""
        if obj.country:
            return obj.country.name
        return None

    def get_role_translated(self, obj):
        """Get the translated role display name"""
        return obj.get_role_display()

    def update(self, instance, validated_data):
        bio = validated_data.pop("bio", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if bio is not None:
            profile, created = instance.profile.get_or_create()
            profile.bio = bio
            profile.save()

        return instance

    def validate_email(self, value):
        """
        Validate that email is unique, excluding the current instance.
        Case insensitive validation.
        """
        if value:

            normalized_email = value.lower().strip()

            instance = getattr(self, "instance", None)

            existing_user = User.objects.filter(email__iexact=normalized_email).first()
            if existing_user and (not instance or existing_user.id != instance.id):
                raise serializers.ValidationError(
                    _("A user with this email already exists.")
                )
        return value

    def validate_phone_number(self, value):
        """
        Validate that phone_number is unique, excluding the current instance.
        """
        if value:

            instance = getattr(self, "instance", None)

            existing_user = User.objects.filter(phone_number=value).first()
            if existing_user and (not instance or existing_user.id != instance.id):
                raise serializers.ValidationError(
                    _("A user with this phone number already exists.")
                )
        return value

    def validate(self, attrs):
        """
        Perform object-level validation.
        """

        if "fullname" in attrs and not attrs["fullname"]:
            raise serializers.ValidationError(
                {"fullname": [_("Fullname cannot be empty.")]}
            )

        if "email" in attrs and attrs["email"]:
            email = attrs["email"].lower().strip()
            attrs["email"] = email

            if "@" not in email or "." not in email.split("@")[-1]:
                raise serializers.ValidationError(
                    {"email": [_("Enter a valid email address.")]}
                )

        if "phone_number" in attrs and attrs["phone_number"]:
            phone = attrs["phone_number"].strip()
            attrs["phone_number"] = phone

            import re

            if not re.match(r"^[\+\-\d\s\(\)]+$", phone):
                raise serializers.ValidationError(
                    {
                        "phone_number": [
                            _(
                                "Phone number can only contain digits, +, -, spaces, and parentheses."
                            )
                        ]
                    }
                )

            digits_only = re.sub(r"[^\d]", "", phone)
            if len(digits_only) < 7:
                raise serializers.ValidationError(
                    {
                        "phone_number": [
                            _("Phone number must contain at least 7 digits.")
                        ]
                    }
                )

        return attrs
