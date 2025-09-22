from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


class BanUserSerializer(serializers.Serializer):
    """
    Serializer for banning a user.

    Validates ban request data including reason and duration.
    """

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text=_("Reason for banning the user (optional)"),
    )

    duration_hours = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=8760,
        help_text=_("Duration of ban in hours (optional, permanent if not provided)"),
    )

    def validate_duration_hours(self, value):
        """Validate duration_hours is a positive integer"""
        if value is not None and value <= 0:
            raise serializers.ValidationError(_("Duration must be a positive number."))
        return value


class BanUserResponseSerializer(serializers.Serializer):
    """
    Serializer for ban user response.

    Documents the response format for successful ban operations.
    """

    detail = serializers.CharField(help_text=_("Success message"))

    user_id = serializers.UUIDField(help_text=_("ID of the banned user"))

    is_banned = serializers.BooleanField(
        help_text=_("Whether the user is currently banned")
    )

    ban_reason = serializers.CharField(
        allow_null=True, help_text=_("Reason for the ban")
    )

    banned_at = serializers.DateTimeField(help_text=_("When the user was banned"))

    banned_by = serializers.UUIDField(
        help_text=_("ID of the admin who banned the user")
    )

    ban_expires_at = serializers.DateTimeField(
        allow_null=True, help_text=_("When the ban expires (null for permanent ban)")
    )

    is_permanent = serializers.BooleanField(
        help_text=_("Whether this is a permanent ban")
    )

    updated_at = serializers.DateTimeField(
        allow_null=True, help_text=_("When the user record was last updated")
    )


class UnbanUserResponseSerializer(serializers.Serializer):
    """
    Serializer for unban user response.

    Documents the response format for successful unban operations.
    """

    detail = serializers.CharField(help_text=_("Success message"))

    user_id = serializers.UUIDField(help_text=_("ID of the unbanned user"))

    is_banned = serializers.BooleanField(
        help_text=_("Whether the user is currently banned (should be False)")
    )

    unbanned_at = serializers.DateTimeField(help_text=_("When the user was unbanned"))

    unbanned_by = serializers.UUIDField(
        help_text=_("ID of the admin who unbanned the user")
    )

    updated_at = serializers.DateTimeField(
        allow_null=True, help_text=_("When the user record was last updated")
    )
