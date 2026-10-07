from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "visibility", "live_url", "created"]
    list_filter = ["visibility"]
    search_fields = ["name", "slug", "repo_full_name", "live_url"]
    raw_id_fields = ["user", "enrollment"]
    readonly_fields = ["ownership_token"]
