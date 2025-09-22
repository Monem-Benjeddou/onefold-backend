from django.contrib import admin
from .models import PrivacyPolicyPoint


@admin.register(PrivacyPolicyPoint)
class PrivacyPolicyPointAdmin(admin.ModelAdmin):
    list_display = ["title", "order"]
    ordering = ["order"]
