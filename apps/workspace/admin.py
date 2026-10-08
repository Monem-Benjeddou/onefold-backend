from django.contrib import admin

from .models import OnboardingDraft


@admin.register(OnboardingDraft)
class OnboardingDraftAdmin(admin.ModelAdmin):
    list_display = ["user", "step", "updated"]
    search_fields = ["user__email"]
    readonly_fields = ["user", "data", "step"]
