"""
Notification Serializers Package

Organized serializers following Django/DRF best practices.
Each serializer is in its own file for better maintainability and readability.
"""

from .user_basic_serializer import UserBasicSerializer
from .notification_serializer import NotificationSerializer
from .notification_detail_serializer import NotificationDetailSerializer
from .notification_list_serializer import NotificationListSerializer
from .notification_create_serializer import NotificationCreateSerializer
from .bulk_notification_action_serializer import BulkNotificationActionSerializer
from .websocket_message_serializer import WebSocketMessageSerializer


NotificationMiniSerializer = NotificationListSerializer

__all__ = [
    "UserBasicSerializer",
    "NotificationSerializer",
    "NotificationDetailSerializer",
    "NotificationListSerializer",
    "NotificationCreateSerializer",
    "BulkNotificationActionSerializer",
    "WebSocketMessageSerializer",
    "NotificationMiniSerializer",
]
