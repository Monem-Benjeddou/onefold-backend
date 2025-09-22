from django.contrib import admin

from .models import User, VerificationCode


class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "code",
    ]
    search_fields = ["id", "user", "code"]
    readonly_fields = ["id"]


class UserAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "email",
        "username",
        "is_staff",
        "is_superuser",
        "is_email_verified",
        "phone_number",
        "role",
        "is_deactivated",
        "is_banned",
        "deactivated_at",
    ]
    search_fields = ["id", "email", "username", "phone_number", "role"]
    list_filter = [
        "is_staff",
        "is_superuser",
        "is_email_verified",
        "role",
        "is_deactivated",
        "is_banned",
    ]
    readonly_fields = ["id", "deactivated_at", "banned_at"]

    fieldsets = (
        (None, {"fields": ("email", "username", "fullname", "password")}),
        ("Personal Info", {"fields": ("phone_number", "avatar", "country", "role")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_email_verified",
                    "is_verified",
                )
            },
        ),
        (
            "Account Status",
            {"fields": ("is_deactivated", "deactivated_at", "deactivation_reason")},
        ),
        (
            "Ban Status",
            {
                "fields": (
                    "is_banned",
                    "banned_at",
                    "ban_reason",
                    "ban_expires_at",
                    "banned_by",
                )
            },
        ),
        ("Important Dates", {"fields": ("created", "updated")}),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:
            readonly.extend(["created", "updated"])
        return readonly

    def save_model(self, request, obj, form, change):
        if "password" in form.changed_data:
            obj.set_password(form.cleaned_data["password"])
        obj.save()


admin.site.register(User, UserAdmin)
admin.site.register(VerificationCode, VerificationCodeAdmin)
