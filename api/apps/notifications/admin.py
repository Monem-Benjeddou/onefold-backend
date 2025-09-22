from django.contrib import admin

from .models import Notification


class NotificationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "body", "created", "updated"]
    search_fields = ["user__username", "body"]
    list_filter = ["created", "updated"]
    readonly_fields = ["created", "updated"]


admin.site.register(Notification, NotificationAdmin)
