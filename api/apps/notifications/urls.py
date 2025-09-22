"""
Notifications URL Configuration

URL patterns for notification management.
"""

from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notification-list"),
    path(
        "<int:pk>/", views.NotificationDetailView.as_view(), name="notification-detail"
    ),
    path("mark-all-read/", views.mark_all_read, name="notification-mark-all-read"),
    path(
        "bulk-action/", views.bulk_notification_action, name="notification-bulk-action"
    ),
    path("stats/", views.notification_stats, name="notification-stats"),
    path("health/", views.health_check, name="health-check"),
]
