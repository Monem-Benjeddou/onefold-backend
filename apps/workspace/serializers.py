from django.utils.text import slugify
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.learning.models import Enrollment
from apps.learning.serializers import EnrollmentSerializer
from apps.projects.serializers import ProjectSerializer

from .starters import OWN_IDEA, STARTER_SLUGS, STARTERS


class WorkspaceSerializer(serializers.Serializer):
    """Everything the app shell needs in one call."""

    user = UserSerializer()
    onboarding_complete = serializers.BooleanField()
    enrollment = EnrollmentSerializer(allow_null=True)
    project = ProjectSerializer(allow_null=True)


class StarterSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    idea = serializers.CharField()
    summary = serializers.CharField()
    builds = serializers.ListField(child=serializers.CharField())


class ChoiceSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class OnboardingStateSerializer(serializers.Serializer):
    complete = serializers.BooleanField()
    step = serializers.IntegerField()
    draft = serializers.DictField()
    starters = StarterSerializer(many=True)
    paces = ChoiceSerializer(many=True)
    experiences = ChoiceSerializer(many=True)


DRAFT_KEYS = {"idea", "pace", "experience", "starter", "project_name", "project_idea"}


class DraftSerializer(serializers.Serializer):
    step = serializers.IntegerField(min_value=1, max_value=4)
    data = serializers.DictField()

    def validate_data(self, value):
        # Only known keys, only short strings: a draft is not free storage.
        return {
            key: str(item)[:300]
            for key, item in value.items()
            if key in DRAFT_KEYS and isinstance(item, str)
        }


class OnboardingSerializer(serializers.Serializer):
    idea = serializers.CharField(max_length=280, required=False, allow_blank=True, default="")
    pace = serializers.ChoiceField(choices=Enrollment.Pace.choices)
    experience = serializers.ChoiceField(choices=Enrollment.Experience.choices)
    starter = serializers.ChoiceField(choices=[*STARTER_SLUGS, OWN_IDEA])
    project_name = serializers.CharField(max_length=80)
    project_idea = serializers.CharField(
        max_length=280, required=False, allow_blank=True, default=""
    )

    def validate_project_name(self, value):
        value = value.strip()
        if not slugify(value):
            raise serializers.ValidationError("Use at least one letter or number.")
        return value

    def validate(self, attrs):
        if attrs["starter"] != OWN_IDEA and not attrs["project_idea"]:
            starter = next(s for s in STARTERS if s["slug"] == attrs["starter"])
            attrs["project_idea"] = starter["idea"]
        if attrs["starter"] == OWN_IDEA and not (attrs["project_idea"] or attrs["idea"]).strip():
            raise serializers.ValidationError(
                {"project_idea": ["Describe your idea in a sentence. You can change it later."]}
            )
        return attrs


class OnboardingResultSerializer(serializers.Serializer):
    enrollment = EnrollmentSerializer()
    project = ProjectSerializer()
