from django.contrib import admin

from .models import CheckRun


@admin.register(CheckRun)
class CheckRunAdmin(admin.ModelAdmin):
    list_display = ["kind", "status", "project", "step", "duration_ms", "created"]
    list_filter = ["status", "kind"]
    search_fields = ["project__name", "step__slug"]
    raw_id_fields = ["project", "step"]
    readonly_fields = [
        "project",
        "step",
        "kind",
        "spec",
        "status",
        "result",
        "duration_ms",
        "started_at",
        "finished_at",
        "idempotency_key",
    ]

    def has_add_permission(self, request):
        return False
