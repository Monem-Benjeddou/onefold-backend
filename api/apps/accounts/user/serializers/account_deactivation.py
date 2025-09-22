"""
Serializers for account deactivation functionality.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class SelfDeactivationRequestSerializer(serializers.Serializer):
    """Serializer for user self-deactivation request."""

    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text=_("Optional reason for deactivating account"),
    )
    confirm_deactivation = serializers.BooleanField(
        required=True, help_text=_("Confirmation that user wants to deactivate account")
    )

    def validate_confirm_deactivation(self, value):
        """Validate that user confirms deactivation."""
        if not value:
            raise serializers.ValidationError(
                _("You must confirm that you want to deactivate your account.")
            )
        return value

    def validate(self, attrs):
        """Validate request data."""
        user = self.context["request"].user

        if not user.is_active:
            raise serializers.ValidationError(
                {"non_field_errors": [_("Account is already deactivated.")]}
            )

        if user.is_superuser:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("Superuser accounts cannot be self-deactivated.")
                    ]
                }
            )

        return attrs


class SelfDeactivationResponseSerializer(serializers.Serializer):
    """Serializer for self-deactivation response."""

    success = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True)
    deactivated_at = serializers.DateTimeField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)


class AccountStatusSerializer(serializers.ModelSerializer):
    """Serializer for displaying account status information."""

    is_active = serializers.BooleanField(read_only=True)
    deactivated_at = serializers.DateTimeField(read_only=True)
    is_banned = serializers.BooleanField(read_only=True)
    banned_at = serializers.DateTimeField(read_only=True)
    ban_reason = serializers.CharField(read_only=True)
    ban_expires_at = serializers.DateTimeField(read_only=True)
    is_currently_banned = serializers.SerializerMethodField()

    def get_is_currently_banned(self, obj):
        """Check if user is currently banned"""
        return obj.is_currently_banned()

    class Meta:
        model = User
        fields = [
            "is_active",
            "deactivated_at",
            "is_banned",
            "banned_at",
            "ban_reason",
            "ban_expires_at",
            "is_currently_banned",
        ]


class UserReactivationSerializer(serializers.Serializer):
    """Serializer for user reactivation (admin use)."""

    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text=_("Optional reason for reactivating account"),
    )

    def validate(self, attrs):
        """Validate reactivation request."""
        user_id = self.context.get("user_id")
        if not user_id:
            raise serializers.ValidationError(_("User ID is required"))

        try:
            user = User.objects.get(id=user_id)
            if user.is_active:
                raise serializers.ValidationError(_("Account is not deactivated."))
        except User.DoesNotExist:
            raise serializers.ValidationError(_("User not found."))

        return attrs
