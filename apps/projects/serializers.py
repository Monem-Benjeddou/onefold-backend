import re
from urllib.parse import urlsplit

from django.utils.text import slugify
from rest_framework import serializers

from apps.learning.services import get_active_enrollment

from .models import Project

REPO_NAME = re.compile(r"^[A-Za-z0-9-]{1,39}/[A-Za-z0-9._-]{1,100}$")


def unique_project_slug(user, name):
    base = slugify(name)[:70] or "project"
    slug, n = base, 2
    while Project.objects.filter(user=user, slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "slug",
            "idea",
            "repo_full_name",
            "live_url",
            "visibility",
            "ownership_token",
            "enrollment",
            "created",
            "updated",
        ]
        read_only_fields = ["id", "slug", "ownership_token", "enrollment", "created", "updated"]

    def validate_name(self, value):
        value = value.strip()
        if not slugify(value):
            raise serializers.ValidationError("Use at least one letter or number.")
        return value

    def validate_repo_full_name(self, value):
        value = value.strip().removeprefix("https://github.com/").rstrip("/").removesuffix(".git")
        if value and not REPO_NAME.match(value):
            raise serializers.ValidationError(
                "Use the GitHub 'owner/repo' form, e.g. ada/habit-loop."
            )
        return value

    def validate_live_url(self, value):
        if not value:
            return value
        parts = urlsplit(value)
        if parts.scheme != "https":
            raise serializers.ValidationError("Use an https:// address. Production apps need TLS.")
        if parts.username or parts.password:
            raise serializers.ValidationError("Remove the username and password from the URL.")
        return value.rstrip("/")

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["user"] = user
        validated_data["slug"] = unique_project_slug(user, validated_data["name"])
        validated_data["enrollment"] = get_active_enrollment(user)
        return super().create(validated_data)
