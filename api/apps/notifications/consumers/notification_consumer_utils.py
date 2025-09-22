"""
Notification Consumer Utility Methods

Utility methods for the NotificationConsumer including database operations,
messaging, and helper functions.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from channels.db import database_sync_to_async
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class NotificationConsumerUtils:
    """Mixin class containing utility methods for NotificationConsumer."""

    async def send_connection_established(self):
        """Send connection established message."""
        try:
            username = (
                self.user.username
                if self.is_authenticated and hasattr(self.user, "username")
                else "Anonymous"
            )
            user_id = (
                str(self.user.id)
                if self.is_authenticated and hasattr(self.user, "id")
                else None
            )

            await self.send_json(
                {
                    "type": "connection_established",
                    "user_id": user_id,
                    "username": username,
                    "is_authenticated": self.is_authenticated,
                    "is_admin": self.is_admin,
                    "groups": list(self.user_groups),
                    "features": [
                        "notifications",
                        "real_time_updates",
                        "ping_pong",
                        "user_groups",
                        "rate_limiting",
                    ],
                    "timestamp": self.get_timestamp(),
                }
            )
        except Exception as e:
            logger.error(
                f"Error sending connection established message: {str(e)}", exc_info=True
            )

            await self.send_json(
                {
                    "type": "connection_established",
                    "user_id": None,
                    "username": "Anonymous",
                    "is_authenticated": False,
                    "is_admin": False,
                    "groups": [],
                    "features": ["ping_pong"],
                    "timestamp": self.get_timestamp(),
                }
            )

    async def send_json(self, content: Dict[str, Any]):
        """Send JSON message with error handling."""
        try:
            await self.send(text_data=json.dumps(content))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}", exc_info=True)

    async def send_error(self, message: str, code: str = "error"):
        """Send error message to client."""
        error_data = {
            "type": "error",
            "code": code,
            "message": message,
            "timestamp": self.get_timestamp(),
        }
        logger.debug(f"Sending error: {error_data}")
        try:

            await self.send(text_data=json.dumps(error_data))
            logger.debug(f"Error sent successfully: {code}")
        except Exception as e:
            logger.error(f"Failed to send error message: {str(e)}", exc_info=True)

            try:
                await self.send(text_data=json.dumps({"type": "error", "code": code}))
            except Exception as fallback_error:
                logger.error(
                    f"Failed to send fallback error message: {str(fallback_error)}",
                    exc_info=True,
                )

    def get_user_identifier(self) -> str:
        """Get user identifier for logging."""
        if self.is_authenticated:
            return f"{self.user.username}_{self.user.id}"

        channel_info = (
            f"_{self.channel_name}"
            if hasattr(self, "channel_name") and self.channel_name
            else ""
        )
        return f"anonymous user{channel_info}"

    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()

    def get_connection_duration(self) -> Optional[str]:
        """Get connection duration as formatted string."""
        if not self.connection_time:
            return None
        delta = datetime.now() - self.connection_time
        return str(delta)

    async def is_rate_limited(self) -> bool:
        """Check if user is rate limited."""
        try:

            user_identifier = self.get_user_identifier()

            sanitized_identifier = "".join(
                c if c.isalnum() else "_" for c in user_identifier
            )
            user_key = f"ws_rate_limit_{sanitized_identifier}"
            current_count = cache.get(user_key, 0)

            if current_count >= 10:
                return True

            cache.set(user_key, current_count + 1, 60)
            return False
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return False

    @database_sync_to_async
    def get_unread_count(self) -> int:
        """Get unread notification count for authenticated user."""
        if not self.is_authenticated:
            return 0

        try:
            from ..models import Notification

            return Notification.objects.filter(
                user=self.user, status=Notification.MARKED_UNREAD
            ).count()
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0

    @database_sync_to_async
    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        if not self.is_authenticated:
            return False

        try:
            from ..models import Notification

            notification = Notification.objects.get(id=notification_id, user=self.user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            logger.warning(
                f"Notification {notification_id} not found for user {self.user.id}"
            )
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False

    @database_sync_to_async
    def mark_all_notifications_read(self) -> int:
        """Mark all notifications as read for authenticated user."""
        if not self.is_authenticated:
            return 0

        try:
            from ..models import Notification

            count = Notification.objects.filter(
                user=self.user, status=Notification.MARKED_UNREAD
            ).update(status=Notification.MARKED_READ, read_at=timezone.now())
            return count
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return 0

    @database_sync_to_async
    def snooze_notification(self, notification_id: str, snooze_until: datetime) -> bool:
        """Snooze notification until specified time."""
        if not self.is_authenticated:
            return False

        try:
            from ..models import Notification

            notification = Notification.objects.get(id=notification_id, user=self.user)
            notification.status = Notification.SNOOZED
            notification.snooze_until = snooze_until
            notification.save(update_fields=["status", "snooze_until"])
            return True
        except Notification.DoesNotExist:
            logger.warning(
                f"Notification {notification_id} not found for user {self.user.id}"
            )
            return False
        except Exception as e:
            logger.error(f"Error snoozing notification: {str(e)}")
            return False
