from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import MagicLink, Session, SignInEvent, SocialAccount, User


class SocialAccountInline(admin.TabularInline):
    model = SocialAccount
    extra = 0
    readonly_fields = ["provider", "uid", "login", "created"]
    can_delete = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-created"]
    list_display = ["email", "name", "email_verified_at", "is_staff", "is_active", "created"]
    search_fields = ["email", "name"]
    fieldsets = [
        (None, {"fields": ["email", "name", "password", "email_verified_at"]}),
        ("Permissions", {"fields": ["is_active", "is_staff", "is_superuser", "groups"]}),
        ("Dates", {"fields": ["last_login", "created"]}),
    ]
    readonly_fields = ["last_login", "created"]
    add_fieldsets = [(None, {"classes": ["wide"], "fields": ["email", "password1", "password2"]})]
    filter_horizontal = ["groups"]
    list_filter = ["is_staff", "is_active"]
    inlines = [SocialAccountInline]


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(MagicLink)
class MagicLinkAdmin(ReadOnlyAdmin):
    list_display = ["email", "purpose", "created", "expires_at", "used_at"]
    list_filter = ["purpose"]
    search_fields = ["email"]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["user", "method", "ip", "user_agent", "last_seen_at", "revoked_at"]
    list_filter = ["method"]
    search_fields = ["user__email", "ip"]
    readonly_fields = ["user", "method", "user_agent", "ip", "created", "last_seen_at"]
    actions = ["revoke"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Sign out the selected sessions")
    def revoke(self, request, queryset):
        from django.utils import timezone

        queryset.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())


@admin.register(SignInEvent)
class SignInEventAdmin(ReadOnlyAdmin):
    list_display = ["created", "kind", "email", "method", "ip"]
    list_filter = ["kind", "method"]
    search_fields = ["email", "ip"]
    date_hierarchy = "created"
