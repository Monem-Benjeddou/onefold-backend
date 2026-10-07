from rest_framework import serializers

from .models import CheckRun


class CheckRunSerializer(serializers.ModelSerializer):
    step = serializers.CharField(source="step.slug", read_only=True)
    project = serializers.UUIDField(source="project_id", read_only=True)

    class Meta:
        model = CheckRun
        fields = [
            "id",
            "project",
            "step",
            "kind",
            "status",
            "result",
            "duration_ms",
            "created",
            "started_at",
            "finished_at",
        ]
        read_only_fields = fields


class CheckRequestSerializer(serializers.Serializer):
    step = serializers.SlugField(help_text="Slug of the step whose check to run")
