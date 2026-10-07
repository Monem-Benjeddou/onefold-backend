"""
Learning paths: what a builder follows from idea to production.

Content is authored as files (see ``apps.learning.content``) and synced into
immutable ``PathVersion`` snapshots. Enrollments pin a version, so editing
content never moves a builder's progress underneath them.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class Path(TimeStampedModel):
    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=200)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.title

    def latest_published_version(self):
        return self.versions.filter(published_at__isnull=False).order_by("-published_at").first()


class PathVersion(TimeStampedModel):
    """An immutable snapshot of a path's content."""

    path = models.ForeignKey(Path, on_delete=models.CASCADE, related_name="versions")
    version = models.CharField(max_length=32)
    title = models.CharField(max_length=200)
    outcome = models.CharField(max_length=300, blank=True)
    content_hash = models.CharField(max_length=64)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["path", "-created"]
        constraints = [
            models.UniqueConstraint(fields=["path", "version"], name="uniq_path_version"),
        ]

    def __str__(self):
        return f"{self.path.slug}@{self.version}"

    @property
    def is_published(self):
        return self.published_at is not None


class Station(TimeStampedModel):
    path_version = models.ForeignKey(PathVersion, on_delete=models.CASCADE, related_name="stations")
    order = models.PositiveSmallIntegerField()
    slug = models.SlugField(max_length=80)
    title = models.CharField(max_length=200)
    role = models.CharField(max_length=80, help_text="The team role this station teaches")

    class Meta:
        ordering = ["path_version", "order"]
        constraints = [
            models.UniqueConstraint(fields=["path_version", "order"], name="uniq_station_order"),
            models.UniqueConstraint(fields=["path_version", "slug"], name="uniq_station_slug"),
        ]

    def __str__(self):
        return f"{self.order:02d} {self.title}"


class Step(TimeStampedModel):
    class Type(models.TextChoices):
        LEARN = "learn", "Learn"
        BUILD = "build", "Build"
        CHECK = "check", "Check"
        SHIP = "ship", "Ship"

    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveSmallIntegerField()
    # Unique across the whole path version so it can address a step in URLs.
    slug = models.SlugField(max_length=80)
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=Type.choices)
    est_minutes = models.PositiveSmallIntegerField()
    requires_laptop = models.BooleanField(default=False)
    body_md = models.TextField(blank=True)
    check_spec = models.JSONField(
        null=True,
        blank=True,
        help_text="Declarative verification spec. Steps with a check can only be "
        "completed by a passing CheckRun.",
    )

    class Meta:
        ordering = ["station__order", "order"]
        constraints = [
            models.UniqueConstraint(fields=["station", "order"], name="uniq_step_order"),
        ]

    def __str__(self):
        return self.title

    @property
    def path_version(self):
        return self.station.path_version

    @property
    def has_check(self):
        return bool(self.check_spec)


class Enrollment(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        SHIPPED = "shipped", "Shipped"
        ABANDONED = "abandoned", "Abandoned"

    class Pace(models.TextChoices):
        LIGHT = "2-4", "2–4 hours a week"
        STEADY = "5-8", "5–8 hours a week"
        INTENSE = "10+", "10+ hours a week"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments"
    )
    path_version = models.ForeignKey(
        PathVersion, on_delete=models.PROTECT, related_name="enrollments"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    pace = models.CharField(max_length=4, choices=Pace.choices, blank=True)

    class Meta:
        ordering = ["-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status="active"),
                name="one_active_enrollment_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.user_id} → {self.path_version}"


class StepProgress(TimeStampedModel):
    class Status(models.TextChoices):
        LOCKED = "locked", "Locked"
        AVAILABLE = "available", "Available"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"
        SKIPPED = "skipped", "Skipped"

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="progress")
    step = models.ForeignKey(Step, on_delete=models.PROTECT, related_name="progress")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.LOCKED)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    # Where the builder left off inside the step (scroll offset), so "Continue"
    # resumes exactly there.
    last_position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["step__station__order", "step__order"]
        constraints = [
            models.UniqueConstraint(fields=["enrollment", "step"], name="uniq_progress_step"),
        ]

    def __str__(self):
        return f"{self.step.slug}: {self.status}"

    @property
    def is_finished(self):
        return self.status in (self.Status.DONE, self.Status.SKIPPED)
