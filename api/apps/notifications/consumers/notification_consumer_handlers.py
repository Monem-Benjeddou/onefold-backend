"""
Notification Consumer Handler Methods

Additional handler methods for the NotificationConsumer.
This file contains the remaining methods to keep the main consumer file manageable.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from channels.db import database_sync_to_async
from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class NotificationConsumerHandlers:
    """Mixin class containing handler methods for NotificationConsumer."""

    async def handle_mark_read(self, data: Dict[str, Any]):
        """Handle marking notification as read."""
        if not self.is_authenticated:
            await self.send_error(_("Authentication required"), "auth_required")
            return

        notification_id = data.get("notification_id")
        if not notification_id:
            await self.send_error(
                _("Notification ID required"), "missing_notification_id"
            )
            return

        try:
            success = await self.mark_notification_read(notification_id)
            if success:
                await self.send_json(
                    {
                        "type": "notification_marked_read",
                        "notification_id": notification_id,
                        "timestamp": self.get_timestamp(),
                    }
                )
            else:
                await self.send_error(
                    _("Failed to mark notification as read"), "mark_read_error"
                )
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            await self.send_error(
                _("Failed to mark notification as read"), "mark_read_error"
            )

    async def handle_mark_all_read(self, data: Dict[str, Any]):
        """Handle marking all notifications as read."""
        if not self.is_authenticated:
            await self.send_error(_("Authentication required"), "auth_required")
            return

        try:
            count = await self.mark_all_notifications_read()
            await self.send_json(
                {
                    "type": "all_notifications_marked_read",
                    "count": count,
                    "timestamp": self.get_timestamp(),
                }
            )
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            await self.send_error(
                _("Failed to mark all notifications as read"), "mark_all_read_error"
            )

    async def handle_snooze_notification(self, data: Dict[str, Any]):
        """Handle snoozing a notification."""
        if not self.is_authenticated:
            await self.send_error(_("Authentication required"), "auth_required")
            return

        notification_id = data.get("notification_id")
        snooze_until_str = data.get("snooze_until")

        if not notification_id or not snooze_until_str:
            await self.send_error(
                _("Notification ID and snooze_until required"), "missing_params"
            )
            return

        try:
            snooze_until = datetime.fromisoformat(
                snooze_until_str.replace("Z", "+00:00")
            )
            success = await self.snooze_notification(notification_id, snooze_until)

            if success:
                await self.send_json(
                    {
                        "type": "notification_snoozed",
                        "notification_id": notification_id,
                        "snooze_until": snooze_until_str,
                        "timestamp": self.get_timestamp(),
                    }
                )
            else:
                await self.send_error(
                    _("Failed to snooze notification"), "snooze_error"
                )
        except ValueError:
            await self.send_error(_("Invalid date format"), "invalid_date")
        except Exception as e:
            logger.error(f"Error snoozing notification: {str(e)}")
            await self.send_error(_("Failed to snooze notification"), "snooze_error")

    async def handle_get_connection_info(self, data: Dict[str, Any]):
        """Handle request for connection information."""
        await self.send_json(
            {
                "type": "connection_info",
                "user_id": str(self.user.id) if self.is_authenticated else None,
                "username": self.user.username if self.is_authenticated else None,
                "is_authenticated": self.is_authenticated,
                "is_admin": self.is_admin,
                "groups": list(self.user_groups),
                "connection_time": (
                    self.connection_time.isoformat() if self.connection_time else None
                ),
                "connection_duration": self.get_connection_duration(),
                "message_count": self.message_count,
                "timestamp": self.get_timestamp(),
            }
        )

    async def notification_created(self, event):
        """Handle new notification event."""
        await self.send_json(event)

    async def notification_updated(self, event):
        """Handle notification update event."""
        await self.send_json(event)

    async def bulk_notification_update(self, event):
        """Handle bulk notification update event."""
        await self.send_json(event)
