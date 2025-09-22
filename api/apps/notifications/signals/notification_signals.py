"""
Notification Signal Handlers

Signal handlers for notification events with WebSocket broadcasting.
Handles real-time notification delivery through Django Channels.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from ..models import Notification


@receiver(post_save, sender=Notification)
def send_notification(sender, instance, created, **kwargs):
    """
    Send real-time notification when a new notification is created.

    Broadcasts notifications to appropriate WebSocket groups:
    - Public notifications: sent to public_notifications_group
    - User notifications: sent to user-specific group

    Args:
        sender: The model class (Notification)
        instance: The notification instance
        created: Boolean indicating if this is a new instance
        **kwargs: Additional signal arguments
    """
    if created:
        channel_layer = get_channel_layer()

        if channel_layer is None:
            return

        if instance.user is None:

            async_to_sync(channel_layer.group_send)(
                "public_notifications_group",
                {
                    "type": "notification_message",
                    "id": str(instance.id),
                    "title": instance.title,
                    "body": instance.body,
                },
            )
        else:

            async_to_sync(channel_layer.group_send)(
                f"user_{str(instance.user.id)}_notifications_group",
                {
                    "type": "user_notification_message",
                    "user": str(instance.user.id),
                    "id": str(instance.id),
                    "title": instance.title,
                    "body": instance.body,
                },
            )
