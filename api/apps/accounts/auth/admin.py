from django.contrib import admin

from .models import OTP

admin.site.register(OTP)


class OTPAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "expires_at")
    search_fields = ("user__email", "code")
    list_filter = ("created_at", "expires_at")
