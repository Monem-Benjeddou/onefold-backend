from django.contrib import admin

from .models import Enrollment, Path, PathVersion, Station, Step, StepProgress


class ReadOnlyContentAdmin(admin.ModelAdmin):
    """Content comes from files via `sync_content`; the admin is for preview only."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Path)
class PathAdmin(admin.ModelAdmin):
    list_display = ["slug", "title", "created"]
    search_fields = ["slug", "title"]


@admin.register(PathVersion)
class PathVersionAdmin(ReadOnlyContentAdmin):
    list_display = ["path", "version", "published_at", "created"]
    list_filter = ["path"]


@admin.register(Station)
class StationAdmin(ReadOnlyContentAdmin):
    list_display = ["order", "title", "role", "path_version"]
    list_filter = ["path_version"]


@admin.register(Step)
class StepAdmin(ReadOnlyContentAdmin):
    list_display = ["slug", "title", "type", "est_minutes", "station"]
    list_filter = ["type", "station__path_version"]
    search_fields = ["slug", "title"]


class StepProgressInline(admin.TabularInline):
    model = StepProgress
    extra = 0
    fields = ["step", "status", "started_at", "completed_at"]
    readonly_fields = fields
    can_delete = False


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["user", "path_version", "status", "pace", "created"]
    list_filter = ["status", "path_version"]
    raw_id_fields = ["user"]
    inlines = [StepProgressInline]
