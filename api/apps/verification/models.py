from django.db import models

from core.abstract.models import AbstractModel


class CheckRun(AbstractModel):
    """
    One execution of a step's check against a project. Append-only: the list of
    runs is the project's verification and deploy history.
    """

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        PASSED = "passed", "Passed"
        # The builder's side: wrong status, app down, token missing.
        FAILED = "failed", "Failed"
        # Our side: a bug or an outage. Never counts against the builder.
        ERROR = "error", "Error"

    FINISHED = (Status.PASSED, Status.FAILED, Status.ERROR)

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="check_runs"
    )
    step = models.ForeignKey(
        "learning.Step", on_delete=models.PROTECT, related_name="check_runs"
    )
    kind = models.CharField(max_length=40)
    spec = models.JSONField(help_text="The spec as it was when the check ran")
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.QUEUED)
    result = models.JSONField(default=dict, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created"]
        indexes = [models.Index(fields=["project", "step", "-created"])]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "idempotency_key"],
                condition=~models.Q(idempotency_key=""),
                name="uniq_check_idempotency_key",
            ),
        ]

    def __str__(self):
        return f"{self.kind} · {self.status}"

    @property
    def is_finished(self):
        return self.status in self.FINISHED
