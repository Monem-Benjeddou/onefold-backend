from django.contrib import admin

from .models import File


class FileAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "created", "updated"]
    search_fields = ["name"]
    list_filter = ["created", "updated"]
    readonly_fields = ["created", "updated"]


admin.site.register(File, FileAdmin)
