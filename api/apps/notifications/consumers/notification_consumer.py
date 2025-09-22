"""
WebSocket Consumer for Notifications

Production-ready notification consumer with comprehensive error handling,
authentication, and connection management.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for notifications.

    Handles public, user-specific, and admin notifications through a single
    connection with proper authentication and role-based access control.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user: Optional[User] = None
        self.user_groups: Set[str] = set()
        self.is_authenticated: bool = False
        self.is_admin: bool = False
        self.connection_time: Optional[datetime] = None
        self.last_ping_time: Optional[datetime] = None
        self.message_count: int = 0

    async def connect(self):
        """
        Handle WebSocket connection with comprehensive authentication and setup.
        """
        try:

            self.user = self.scope.get("user")
            self.is_authenticated = self.user and not isinstance(
                self.user, AnonymousUser
            )
            self.is_admin = self.is_authenticated and (
                self.user.is_staff or self.user.is_superuser
            )
            self.connection_time = datetime.now()

            await self.setup_user_groups()

            await self.accept()

            await self.join_user_groups()

            await self.send_connection_established()

            user_info = (
                f"user {self.user.username} (ID: {self.user.id})"
                if self.is_authenticated
                else "anonymous user"
            )
            logger.info(
                f"WebSocket connected: {user_info}, groups: {list(self.user_groups)}"
            )

        except Exception as e:
            logger.error(f"Error during WebSocket connection: {str(e)}", exc_info=True)

            try:
                await self.accept()
                await self.send_error(
                    "Service temporarily degraded - some features may be limited",
                    "service_degraded",
                )
            except Exception as accept_error:
                logger.error(f"Failed to accept connection: {str(accept_error)}")
                await self.close(code=4000)

    async def join_user_groups(self):
        """
        Join user groups with Redis error handling.
        """
        if not hasattr(self, "channel_layer") or not self.channel_layer:
            logger.warning(
                "No channel layer available - WebSocket will work without group features"
            )
            return

        for group_name in self.user_groups:
            try:
                await self.channel_layer.group_add(group_name, self.channel_name)
                logger.debug(f"Joined group: {group_name}")
            except Exception as e:
                logger.error(f"Failed to join group {group_name}: {str(e)}")

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection with proper cleanup.
        """
        try:

            await self.leave_user_groups()

            duration = None
            if self.connection_time:
                duration = datetime.now() - self.connection_time

            user_info = (
                f"user {self.user.username}"
                if self.is_authenticated
                else "anonymous user"
            )
            logger.info(
                f"WebSocket disconnected: {user_info}, code: {close_code}, duration: {duration}, messages: {self.message_count}"
            )

        except Exception as e:
            logger.error(
                f"Error during WebSocket disconnection: {str(e)}", exc_info=True
            )
        finally:

            self.user_groups.clear()
            self.user = None
            self.connection_time = None

    async def leave_user_groups(self):
        """
        Leave user groups with Redis error handling.
        """
        if not hasattr(self, "channel_layer") or not self.channel_layer:
            return

        for group_name in self.user_groups:
            try:
                await self.channel_layer.group_discard(group_name, self.channel_name)
                logger.debug(f"Left group: {group_name}")
            except Exception as e:
                logger.error(f"Failed to leave group {group_name}: {str(e)}")

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages with comprehensive validation.
        """
        try:
            logger.debug(f"Received WebSocket message: {text_data}")

            try:
                data = json.loads(text_data)
                logger.debug(f"Parsed JSON data: {data}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format: {text_data}")
                await self.send_error(_("Invalid JSON format"), "invalid_json")
                return

            message_type = data.get("type")
            if not message_type:
                logger.error(f"Message missing type field: {data}")
                await self.send_error(_("Message type is required"), "missing_type")
                return

            logger.debug(f"Processing message type: {message_type}")

            self.message_count += 1

            rate_limited = await self.is_rate_limited()
            logger.debug(f"Rate limit check result: {rate_limited}")
            if rate_limited:
                logger.debug("Message rate limited - sending error response")
                await self.send_error(_("Rate limit exceeded"), "rate_limit")
                return

            logger.debug(f"Handling message: {message_type}")
            await self.handle_message(message_type, data)

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}", exc_info=True)
            await self.send_error(_("Internal server error"), "server_error")

    async def setup_user_groups(self):
        """
        Setup user groups based on authentication and roles.
        """

        self.user_groups.add("notifications_public")

        if self.is_authenticated:

            self.user_groups.add("notifications_authenticated")

            self.user_groups.add(f"user_{self.user.id}")

            if self.is_admin:
                self.user_groups.add("notifications_admin")
                if self.user.is_superuser:
                    self.user_groups.add("notifications_superadmin")

    async def handle_message(self, message_type: str, data: Dict[str, Any]):
        """
        Route messages to appropriate handlers.
        """

        if message_type == "ping":
            await self.handle_ping(data)

        elif message_type == "get_unread_count":
            await self.handle_get_unread_count(data)
        elif message_type == "mark_read":
            await self.handle_mark_read(data)
        elif message_type == "mark_all_read":
            await self.handle_mark_all_read(data)
        elif message_type == "snooze_notification":
            await self.handle_snooze_notification(data)
        elif message_type == "get_connection_info":
            await self.handle_get_connection_info(data)

        else:
            await self.send_error(
                _("Unknown message type: {type}").format(type=message_type),
                "unknown_type",
            )

    async def handle_ping(self, data: Dict[str, Any]):
        """Handle ping message for connection health check."""
        self.last_ping_time = datetime.now()
        await self.send_json(
            {
                "type": "pong",
                "timestamp": self.get_timestamp(),
                "server_time": self.get_timestamp(),
                "connection_duration": self.get_connection_duration(),
            }
        )

    async def handle_get_unread_count(self, data: Dict[str, Any]):
        """Handle request for unread notification count."""
        logger.debug(
            f"handle_get_unread_count called, is_authenticated: {self.is_authenticated}"
        )
        if not self.is_authenticated:
            logger.debug("Sending auth_required error")
            await self.send_error(_("Authentication required"), "auth_required")
            return

        try:
            count = await self.get_unread_count()
            logger.debug(f"Got unread count: {count}")
            await self.send_json(
                {
                    "type": "unread_count",
                    "count": count,
                    "timestamp": self.get_timestamp(),
                }
            )
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            await self.send_error(_("Failed to get unread count"), "unread_count_error")


from .notification_consumer_handlers import NotificationConsumerHandlers
from .notification_consumer_utils import NotificationConsumerUtils


class NotificationConsumerComplete(
    NotificationConsumer, NotificationConsumerHandlers, NotificationConsumerUtils
):
    """
    Complete NotificationConsumer with all handler and utility methods.

    This class combines the base consumer with handler and utility mixins
    to provide a full-featured WebSocket consumer for notifications.
    """

    pass


NotificationConsumer = NotificationConsumerComplete
