"""
Notification Views Package

Organized views following Django/DRF best practices with separation of concerns.
Each view is in its own file for better maintainability and readability.
"""

from .notification_list_view import NotificationListView
from .notification_detail_view import NotificationDetailView
from .bulk_notification_action_view import bulk_notification_action
from .notification_stats_view import notification_stats
from .mark_all_read_view import mark_all_read
from .health_check_view import health_check
from core.abstract.paginations import MetaPageNumberPagination


NotificationAPIView = NotificationDetailView

__all__ = [
    "NotificationListView",
    "NotificationDetailView",
    "NotificationAPIView",
    "bulk_notification_action",
    "notification_stats",
    "mark_all_read",
    "health_check",
    "MetaPageNumberPagination",
]
