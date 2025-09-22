"""
Notification Service

Service class for managing notification functionality with business logic separation.
Provides comprehensive notification management with real-time WebSocket broadcasting.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from ..models import Notification

User = get_user_model()
logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


class NotificationService:
    """
    Service for managing notifications.

    Provides business logic for notification operations including:
    - Creating notifications with real-time delivery
    - Managing notification status (read/unread/snoozed)
    - Bulk operations on notifications
    - WebSocket broadcasting for real-time updates
    """

    @classmethod
    def create_notification(
        cls,
        user: User,
        title: str,
        body: str,
        notification_type: str = "system",
        priority: str = "normal",
        content_object=None,
        action_url: str = None,
        metadata: Dict = None,
        expires_at: datetime = None,
    ) -> Notification:
        """
        Create and send a notification to a user.

        Args:
            user: Target user for the notification
            title: Notification title
            body: Notification body text
            notification_type: Type of notification (default: "system")
            priority: Priority level (default: "normal")
            content_object: Related object (optional)
            action_url: URL for notification action (optional)
            metadata: Additional metadata dict (optional)
            expires_at: Expiration datetime (optional)

        Returns:
            Created Notification instance

        Raises:
            Exception: If notification creation fails
        """
        try:
            with transaction.atomic():
                notification = Notification.objects.create(
                    user=user,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    priority=priority,
                    content_object=content_object,
                    action_url=action_url,
                    metadata=metadata or {},
                    expires_at=expires_at,
                )

                cls._send_realtime_notification(notification)

                return notification

        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise

    @classmethod
    def mark_notification_read(cls, notification: Notification, user: User) -> bool:
        """
        Mark a notification as read.

        Args:
            notification: Notification to mark as read
            user: User performing the action

        Returns:
            True if successful, False otherwise
        """
        try:
            if notification.user != user:
                return False

            notification.mark_as_read()
            cls._broadcast_notification_update(notification, "read")
            return True

        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False

    @classmethod
    def mark_all_read(cls, user: User) -> int:
        """
        Mark all unread notifications as read for a user.

        Args:
            user: User whose notifications to mark as read

        Returns:
            Number of notifications marked as read
        """
        try:
            unread_notifications = Notification.objects.filter(
                user=user, status=Notification.MARKED_UNREAD
            )

            count = unread_notifications.update(
                status=Notification.MARKED_READ, read_at=timezone.now()
            )

            if count > 0:
                cls._broadcast_bulk_notification_update(user, "mark_all_read", count)

            return count

        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return 0

    @classmethod
    def get_unread_count(cls, user: User) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user: User to get unread count for

        Returns:
            Number of unread notifications
        """
        try:
            return Notification.objects.filter(
                user=user, status=Notification.MARKED_UNREAD
            ).count()

        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0

    @classmethod
    def snooze_notification(
        cls, notification: Notification, user: User, snooze_until: datetime
    ) -> bool:
        """
        Snooze a notification until a specific time.

        Args:
            notification: Notification to snooze
            user: User performing the action
            snooze_until: Datetime when notification should reappear

        Returns:
            True if successful, False otherwise
        """
        try:
            if notification.user != user:
                return False

            notification.status = Notification.SNOOZED
            notification.snooze_until = snooze_until
            notification.save(update_fields=["status", "snooze_until"])

            cls._broadcast_notification_update(notification, "snoozed")
            return True

        except Exception as e:
            logger.error(f"Error snoozing notification: {str(e)}")
            return False

    @classmethod
    def _send_realtime_notification(cls, notification: Notification):
        """
        Send real-time notification via WebSocket.

        Args:
            notification: Notification to broadcast
        """
        if not channel_layer:
            return

        try:

            notification.mark_as_delivered()

            message = {
                "type": "notification_created",
                "notification": {
                    "id": notification.id,
                    "title": notification.title,
                    "body": notification.body,
                    "notification_type": notification.notification_type,
                    "priority": notification.priority,
                    "action_url": notification.action_url,
                    "metadata": notification.metadata,
                    "created": notification.created.isoformat(),
                },
            }

            async_to_sync(channel_layer.group_send)(
                f"user_{notification.user.id}", message
            )

            if notification.notification_type in ["system", "announcement"]:
                async_to_sync(channel_layer.group_send)(
                    "notifications_authenticated", message
                )

        except Exception as e:
            logger.error(f"Error sending real-time notification: {str(e)}")

    @classmethod
    def _broadcast_notification_update(
        cls, notification: Notification, update_type: str
    ):
        """
        Broadcast notification status updates.

        Args:
            notification: Updated notification
            update_type: Type of update performed
        """
        if not channel_layer:
            return

        try:
            message = {
                "type": "notification_updated",
                "notification_id": notification.id,
                "update_type": update_type,
                "status": notification.status,
                "read_at": (
                    notification.read_at.isoformat() if notification.read_at else None
                ),
            }

            async_to_sync(channel_layer.group_send)(
                f"user_{notification.user.id}", message
            )

        except Exception as e:
            logger.error(f"Error broadcasting notification update: {str(e)}")

    @classmethod
    def _broadcast_bulk_notification_update(
        cls, user: User, update_type: str, count: int
    ):
        """
        Broadcast bulk notification updates.

        Args:
            user: User whose notifications were updated
            update_type: Type of bulk update performed
            count: Number of notifications affected
        """
        if not channel_layer:
            return

        try:
            message = {
                "type": "bulk_notification_update",
                "update_type": update_type,
                "count": count,
                "unread_count": cls.get_unread_count(user),
            }

            async_to_sync(channel_layer.group_send)(f"user_{user.id}", message)

        except Exception as e:
            logger.error(f"Error broadcasting bulk notification update: {str(e)}")
