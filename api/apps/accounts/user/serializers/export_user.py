from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from core.abstract.serializers import AbstractSerializer
from apps.accounts.user.models import User
from apps.accounts.user.constants import ROLE_CHOICES


class UserExportSerializer(AbstractSerializer):
    country_name = serializers.SerializerMethodField()
    role_translated = serializers.SerializerMethodField()
    created = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_country_name(self, obj):
        if obj.country:
            return obj.country.name
        return None

    def get_role_translated(self, obj):
        role_choices = dict(ROLE_CHOICES)
        if obj.role in role_choices:
            return _(role_choices[obj.role])
        return obj.role

    def get_created(self, obj):
        if obj.created:
            return obj.created.isoformat()
        return None

    def get_created_at(self, obj):
        """Alias for created field for backward compatibility"""
        if obj.created:
            return obj.created.isoformat()
        return None

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "fullname",
            "phone_number",
            "country",
            "country_name",
            "role",
            "role_translated",
            "is_staff",
            "created",
            "created_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data["avatar"] = (
                self.context["request"].build_absolute_uri(instance.avatar.url)
                if instance.avatar
                else None
            )
        except (AttributeError, ValueError, KeyError):
            data["avatar"] = None
        return data
