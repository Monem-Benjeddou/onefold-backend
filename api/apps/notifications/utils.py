"""
Notification Utilities

Production-ready utilities for creating and sending notifications
with proper error handling, logging, and WebSocket integration.
"""

import logging
from typing import Optional, Dict, Any, List, Union
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from .serializers import NotificationCreateSerializer

User = get_user_model()
logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


class NotificationSender:
    """
    Production-ready notification sender with comprehensive error handling.
    """

    @staticmethod
    def send_notification(
        user: User,
        title: str,
        body: str,
        status: str = "u",
        notification_type: str = None,
        metadata: Dict[str, Any] = None,
        save_to_db: bool = True,
        send_websocket: bool = True,
        priority: str = "normal",
    ) -> Optional[Any]:
        """
        Send notification to a specific user.

        Args:
            user: Target user
            title: Notification title
            body: Notification body
            status: Notification status ('u' for unread, 'r' for read)
            notification_type: Type of notification (e.g., 'topic_created', 'post_reply')
            metadata: Additional metadata for the notification
            save_to_db: Whether to save notification to database
            send_websocket: Whether to send via WebSocket
            priority: Notification priority ('low', 'normal', 'high', 'critical')

        Returns:
            Created notification instance or None if failed
        """
        if not user or not title:
            logger.warning("Invalid user or title provided to send_notification")
            return None

        notification = None
        metadata = metadata or {}

        try:

            if save_to_db:
                notification = NotificationSender._save_notification(
                    user=user, title=title, body=body, status=status
                )

                if not notification:
                    logger.error(
                        f"Failed to save notification to database for user {user.id}"
                    )
                    if not send_websocket:
                        return None

            if send_websocket and channel_layer:
                NotificationSender._send_websocket_notification(
                    user=user,
                    title=title,
                    body=body,
                    status=status,
                    notification_type=notification_type,
                    metadata=metadata,
                    priority=priority,
                    notification_id=str(notification.id) if notification else None,
                    created=notification.created.isoformat() if notification else None,
                )

            logger.info(
                f"Successfully sent notification '{title}' to user {user.username} (ID: {user.id})"
            )
            return notification

        except Exception as e:
            logger.error(
                f"Error sending notification to user {user.id}: {str(e)}", exc_info=True
            )
            return None

    @staticmethod
    def send_bulk_notifications(
        users: List[User],
        title: str,
        body: str,
        status: str = "u",
        notification_type: str = None,
        metadata: Dict[str, Any] = None,
        save_to_db: bool = True,
        send_websocket: bool = True,
        priority: str = "normal",
    ) -> Dict[str, Any]:
        """
        Send notifications to multiple users efficiently.

        Returns:
            Dictionary with success/failure counts and any errors
        """
        if not users or not title:
            logger.warning(
                "Invalid users list or title provided to send_bulk_notifications"
            )
            return {"success": 0, "failed": 0, "errors": ["Invalid input"]}

        results = {"success": 0, "failed": 0, "errors": []}
        notifications = []

        try:

            if save_to_db:
                notifications = NotificationSender._bulk_save_notifications(
                    users=users, title=title, body=body, status=status
                )

            if send_websocket and channel_layer:
                for i, user in enumerate(users):
                    try:
                        notification = (
                            notifications[i] if i < len(notifications) else None
                        )
                        NotificationSender._send_websocket_notification(
                            user=user,
                            title=title,
                            body=body,
                            status=status,
                            notification_type=notification_type,
                            metadata=metadata,
                            priority=priority,
                            notification_id=(
                                str(notification.id) if notification else None
                            ),
                            created=(
                                notification.created.isoformat()
                                if notification
                                else None
                            ),
                        )
                        results["success"] += 1
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append(f"User {user.id}: {str(e)}")
                        logger.error(
                            f"Failed to send WebSocket notification to user {user.id}: {str(e)}"
                        )
            else:
                results["success"] = len(notifications)

            logger.info(
                f"Bulk notification '{title}' sent: {results['success']} success, {results['failed']} failed"
            )

        except Exception as e:
            logger.error(f"Error in bulk notification sending: {str(e)}", exc_info=True)
            results["errors"].append(f"Bulk operation failed: {str(e)}")
            results["failed"] = len(users)

        return results

    @staticmethod
    def send_admin_notification(
        title: str,
        body: str,
        notification_type: str = None,
        metadata: Dict[str, Any] = None,
        priority: str = "normal",
        target_roles: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Send notification to admin users (staff, superusers, specific roles).

        Args:
            target_roles: List of roles to target (e.g., ['admin', 'moderator'])
        """
        try:

            admin_users = NotificationSender._get_admin_users(target_roles)

            if not admin_users:
                logger.warning("No admin users found for notification")
                return {"success": 0, "failed": 0, "errors": ["No admin users found"]}

            results = NotificationSender.send_bulk_notifications(
                users=admin_users,
                title=title,
                body=body,
                notification_type=notification_type,
                metadata=metadata,
                priority=priority,
            )

            if channel_layer:
                try:
                    async_to_sync(channel_layer.group_send)(
                        "admin_notifications_group",
                        {
                            "type": "admin_notification_message",
                            "id": None,
                            "title": title,
                            "body": body,
                            "status": "u",
                            "created": None,
                            "notification_type": notification_type,
                            "metadata": metadata or {},
                            "priority": priority,
                        },
                    )
                except Exception as e:
                    logger.error(f"Failed to send admin group notification: {str(e)}")

            return results

        except Exception as e:
            logger.error(f"Error sending admin notification: {str(e)}", exc_info=True)
            return {"success": 0, "failed": 1, "errors": [str(e)]}

    @staticmethod
    def send_public_notification(
        title: str,
        body: str,
        notification_type: str = None,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """
        Send public notification to all connected clients.
        """
        if not channel_layer:
            logger.warning("Channel layer not available for public notification")
            return False

        try:
            async_to_sync(channel_layer.group_send)(
                "public_notifications_group",
                {
                    "type": "public_notification_message",
                    "id": None,
                    "title": title,
                    "body": body,
                    "created": None,
                    "notification_type": notification_type,
                    "metadata": metadata or {},
                },
            )

            logger.info(f"Sent public notification: '{title}'")
            return True

        except Exception as e:
            logger.error(f"Error sending public notification: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def _save_notification(user: User, title: str, body: str, status: str):
        """Save notification to database with error handling."""
        try:
            with transaction.atomic():
                data = {"user": user.id, "title": title, "body": body, "status": status}
                serializer = NotificationCreateSerializer(data=data)
                if serializer.is_valid():
                    return serializer.save()
                else:
                    logger.error(
                        f"Notification serializer validation failed: {serializer.errors}"
                    )

                    from .models import Notification

                    return Notification.objects.create(
                        user=user, title=title, body=body, status=status
                    )
        except Exception as e:
            logger.error(f"Error saving notification to database: {str(e)}")
            return None

    @staticmethod
    def _bulk_save_notifications(
        users: List[User], title: str, body: str, status: str
    ) -> List:
        """Bulk save notifications to database."""
        try:
            from .models import Notification

            notifications = []
            with transaction.atomic():
                for user in users:
                    notification = Notification(
                        user=user, title=title, body=body, status=status
                    )
                    notifications.append(notification)

                created_notifications = Notification.objects.bulk_create(notifications)
                logger.info(f"Bulk created {len(created_notifications)} notifications")
                return created_notifications

        except Exception as e:
            logger.error(f"Error bulk saving notifications: {str(e)}")
            return []

    @staticmethod
    def _send_websocket_notification(
        user: User,
        title: str,
        body: str,
        status: str,
        notification_type: str,
        metadata: Dict[str, Any],
        priority: str,
        notification_id: str = None,
        created: str = None,
    ):
        """Send notification via WebSocket."""
        try:
            group_name = f"user_{user.id}_notifications_group"

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "user_notification_message",
                    "user_id": str(user.id),
                    "id": notification_id,
                    "title": title,
                    "body": body,
                    "status": status,
                    "created": created,
                    "notification_type": notification_type,
                    "metadata": metadata,
                    "priority": priority,
                },
            )

        except Exception as e:
            logger.error(
                f"Error sending WebSocket notification to user {user.id}: {str(e)}"
            )
            raise

    @staticmethod
    def _get_admin_users(target_roles: List[str] = None) -> List[User]:
        """Get admin users based on roles."""
        try:
            from django.db.models import Q

            query = Q(is_staff=True) | Q(is_superuser=True)

            if target_roles and hasattr(User, "role"):
                role_query = Q(role__in=target_roles)
                query = query | role_query

            return list(User.objects.filter(query).distinct())

        except Exception as e:
            logger.error(f"Error getting admin users: {str(e)}")
            return []


def push_notifications(
    user, title, body, status="u", notification_type=None, metadata=None
):
    """
    Legacy function for backward compatibility.
    """
    return NotificationSender.send_notification(
        user=user,
        title=title,
        body=body,
        status=status,
        notification_type=notification_type,
        metadata=metadata,
    )


def send_notification_to_users(
    users, title, body, status="u", notification_type=None, metadata=None
):
    """
    Send notification to multiple users.
    """
    return NotificationSender.send_bulk_notifications(
        users=users,
        title=title,
        body=body,
        status=status,
        notification_type=notification_type,
        metadata=metadata,
    )


def send_admin_notification(
    title, body, notification_type=None, metadata=None, priority="normal"
):
    """
    Send notification to all admin users.
    """
    return NotificationSender.send_admin_notification(
        title=title,
        body=body,
        notification_type=notification_type,
        metadata=metadata,
        priority=priority,
    )


def send_public_notification(title, body, notification_type=None, metadata=None):
    """
    Send public notification to all connected clients.
    """
    return NotificationSender.send_public_notification(
        title=title, body=body, notification_type=notification_type, metadata=metadata
    )
