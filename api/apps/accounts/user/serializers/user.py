from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from core.abstract.serializers import AbstractSerializer
from apps.accounts.user.models import User
from apps.accounts.user.constants import ROLE_CHOICES


class UserSerializer(AbstractSerializer):

    country_name = serializers.ReadOnlyField(
        source="country.name", allow_null=True, default=None
    )
    role_translated = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False)

    is_currently_banned = serializers.ReadOnlyField(default=False)
    banned_by_username = serializers.ReadOnlyField(
        source="banned_by.username", allow_null=True, default=None
    )
    is_account_active = serializers.ReadOnlyField(default=True)

    def get_role_translated(self, obj):
        role_choices = dict(ROLE_CHOICES)
        if obj.role in role_choices:
            return _(role_choices[obj.role])
        return obj.role if obj.role in role_choices else "user"

    class Meta:
        model = User
        fields = [
            "_id",
            "id",
            "email",
            "username",
            "password",
            "fullname",
            "phone_number",
            "role",
            "role_translated",
            "country",
            "country_name",
            "avatar",
            "date_of_birth",
            "is_staff",
            "is_superuser",
            "is_banned",
            "is_currently_banned",
            "ban_reason",
            "banned_at",
            "banned_by_username",
            "ban_expires_at",
            "is_verified",
            "is_deactivated",
            "deactivated_at",
            "deactivation_reason",
            "is_account_active",
        ]
        read_only_fields = [
            "id",
            "date_of_birth",
            "is_currently_banned",
            "banned_by_username",
            "is_banned",
            "ban_reason",
            "banned_at",
            "ban_expires_at",
            "is_deactivated",
            "deactivated_at",
            "deactivation_reason",
            "is_account_active",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data["avatar"] = (
                self.context["request"].build_absolute_uri(instance.avatar.url)
                if instance.avatar
                else None
            )
        except (AttributeError, ValueError, KeyError):
            try:
                data["avatar"] = instance.avatar.url
            except:
                data["avatar"] = None

        return data
