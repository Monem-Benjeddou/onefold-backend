from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import MagicLink, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-created"]
    list_display = ["email", "name", "is_staff", "is_active", "created"]
    search_fields = ["email", "name"]
    fieldsets = [
        (None, {"fields": ["email", "name", "password"]}),
        ("Permissions", {"fields": ["is_active", "is_staff", "is_superuser", "groups"]}),
        ("Dates", {"fields": ["last_login", "created"]}),
    ]
    readonly_fields = ["last_login", "created"]
    add_fieldsets = [(None, {"classes": ["wide"], "fields": ["email", "password1", "password2"]})]
    filter_horizontal = ["groups"]
    list_filter = ["is_staff", "is_active"]


@admin.register(MagicLink)
class MagicLinkAdmin(admin.ModelAdmin):
    list_display = ["email", "created", "expires_at", "used_at"]
    search_fields = ["email"]
    readonly_fields = ["email", "token_hash", "expires_at", "used_at"]

    def has_add_permission(self, request):
        return False
