from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Enrollment, PathVersion, Station, Step, StepProgress


class StepOutlineSerializer(serializers.ModelSerializer):
    has_check = serializers.BooleanField(read_only=True)

    class Meta:
        model = Step
        fields = ["slug", "title", "type", "est_minutes", "requires_laptop", "has_check"]


class StationOutlineSerializer(serializers.ModelSerializer):
    steps = StepOutlineSerializer(many=True, read_only=True)

    class Meta:
        model = Station
        fields = ["order", "slug", "title", "role", "steps"]


class PathVersionSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(source="path.slug", read_only=True)

    class Meta:
        model = PathVersion
        fields = ["slug", "version", "title", "outcome"]


class PathOutlineSerializer(PathVersionSerializer):
    stations = StationOutlineSerializer(many=True, read_only=True)

    class Meta(PathVersionSerializer.Meta):
        fields = PathVersionSerializer.Meta.fields + ["stations"]


class StepProgressSummarySerializer(serializers.ModelSerializer):
    slug = serializers.CharField(source="step.slug", read_only=True)
    station = serializers.IntegerField(source="step.station.order", read_only=True)

    class Meta:
        model = StepProgress
        fields = ["slug", "station", "status", "started_at", "completed_at"]


class NextStepSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(source="step.slug", read_only=True)
    title = serializers.CharField(source="step.title", read_only=True)
    type = serializers.CharField(source="step.type", read_only=True)
    est_minutes = serializers.IntegerField(source="step.est_minutes", read_only=True)
    station_order = serializers.IntegerField(source="step.station.order", read_only=True)
    station_title = serializers.CharField(source="step.station.title", read_only=True)

    class Meta:
        model = StepProgress
        fields = [
            "slug",
            "title",
            "type",
            "est_minutes",
            "station_order",
            "station_title",
            "status",
            "last_position",
        ]


class TotalsSerializer(serializers.Serializer):
    done = serializers.IntegerField()
    total = serializers.IntegerField()


class StationRefSerializer(serializers.Serializer):
    order = serializers.IntegerField()
    slug = serializers.CharField()
    title = serializers.CharField()
    role = serializers.CharField()


class EnrollmentSerializer(serializers.ModelSerializer):
    path = PathVersionSerializer(source="path_version", read_only=True)
    next_step = serializers.SerializerMethodField()
    steps = serializers.SerializerMethodField()
    totals = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ["id", "status", "pace", "created", "path", "next_step", "steps", "totals"]

    def _progress(self, obj):
        if not hasattr(obj, "_progress_cache"):
            obj._progress_cache = list(obj.progress.select_related("step__station"))
        return obj._progress_cache

    @extend_schema_field(NextStepSerializer(allow_null=True))
    def get_next_step(self, obj):
        progress = self._progress(obj)
        upcoming = next(
            (p for p in progress if p.status == StepProgress.Status.IN_PROGRESS), None
        ) or next((p for p in progress if p.status == StepProgress.Status.AVAILABLE), None)
        return NextStepSerializer(upcoming).data if upcoming else None

    @extend_schema_field(StepProgressSummarySerializer(many=True))
    def get_steps(self, obj):
        return StepProgressSummarySerializer(self._progress(obj), many=True).data

    @extend_schema_field(TotalsSerializer)
    def get_totals(self, obj):
        progress = self._progress(obj)
        return {"done": sum(p.is_finished for p in progress), "total": len(progress)}


class EnrollRequestSerializer(serializers.Serializer):
    pace = serializers.ChoiceField(choices=Enrollment.Pace.choices, required=False, default="")


class CheckSummarySerializer(serializers.Serializer):
    """What "Check my work" will do, shown before it runs."""

    kind = serializers.CharField()
    statement = serializers.CharField(required=False, help_text="attest: what the builder confirms")
    url = serializers.CharField(required=False, help_text="http.get: the URL template we call")
    expect_status = serializers.IntegerField(required=False)
    expect_body_contains = serializers.CharField(required=False)


class StepRefSerializer(serializers.Serializer):
    slug = serializers.CharField()
    title = serializers.CharField()
    status = serializers.CharField()


class StepDetailSerializer(serializers.ModelSerializer):
    """A step as the builder sees it, with their progress attached."""

    slug = serializers.CharField(source="step.slug", read_only=True)
    title = serializers.CharField(source="step.title", read_only=True)
    type = serializers.CharField(source="step.type", read_only=True)
    est_minutes = serializers.IntegerField(source="step.est_minutes", read_only=True)
    requires_laptop = serializers.BooleanField(source="step.requires_laptop", read_only=True)
    body_md = serializers.CharField(source="step.body_md", read_only=True)
    has_check = serializers.BooleanField(source="step.has_check", read_only=True)
    station = serializers.SerializerMethodField()
    check = serializers.SerializerMethodField()
    previous = serializers.SerializerMethodField()
    next = serializers.SerializerMethodField()

    class Meta:
        model = StepProgress
        fields = [
            "slug",
            "title",
            "type",
            "est_minutes",
            "requires_laptop",
            "has_check",
            "body_md",
            "station",
            "check",
            "status",
            "started_at",
            "completed_at",
            "last_position",
            "previous",
            "next",
        ]
        read_only_fields = ["status", "started_at", "completed_at"]

    def _neighbours(self, obj):
        if not hasattr(obj, "_neighbours"):
            ordered = list(
                obj.enrollment.progress.select_related("step").order_by(
                    "step__station__order", "step__order"
                )
            )
            index = next(i for i, p in enumerate(ordered) if p.pk == obj.pk)
            obj._neighbours = (
                ordered[index - 1] if index > 0 else None,
                ordered[index + 1] if index + 1 < len(ordered) else None,
            )
        return obj._neighbours

    @staticmethod
    def _ref(progress):
        if progress is None:
            return None
        return {"slug": progress.step.slug, "title": progress.step.title, "status": progress.status}

    @extend_schema_field(StepRefSerializer(allow_null=True))
    def get_previous(self, obj):
        return self._ref(self._neighbours(obj)[0])

    @extend_schema_field(StepRefSerializer(allow_null=True))
    def get_next(self, obj):
        return self._ref(self._neighbours(obj)[1])

    @extend_schema_field(StationRefSerializer)
    def get_station(self, obj):
        return StationRefSerializer(obj.step.station).data

    @extend_schema_field(CheckSummarySerializer(allow_null=True))
    def get_check(self, obj):
        spec = obj.step.check_spec
        if not spec:
            return None
        summary = {"kind": spec["kind"]}
        if "statement" in spec:
            summary["statement"] = spec["statement"]
        if "url" in spec:
            summary["url"] = spec["url"]
            expect = spec.get("expect", {})
            summary["expect_status"] = expect.get("status", 200)
            if expect.get("body_contains"):
                summary["expect_body_contains"] = expect["body_contains"]
        return summary
