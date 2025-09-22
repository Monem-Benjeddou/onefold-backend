from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from core.tasks.emails import send_email_with_html
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_notification(
    user_id, title, message, notification_type="info", email_notification=False
):
    """
    Send notification to user with optional email notification.

    Args:
        user_id: ID of the user to notify
        title: Notification title
        message: Notification message
        notification_type: Type of notification (info, success, warning, error)
        email_notification: Whether to also send email notification
    """
    try:
        from django.contrib.auth import get_user_model
        from apps.notifications.models import Notification

        User = get_user_model()
        user = User.objects.get(id=user_id)

        notification = Notification.objects.create(
            user=user, title=title, message=message, notification_type=notification_type
        )

        if email_notification and user.email:
            email_context = {
                "user": user,
                "title": title,
                "message": message,
                "notification_type": notification_type,
            }

            send_email_with_html.delay(
                subject=f"cards Platform - {title}",
                html_template_name="notifications/email_notification.html",
                recipients=[user.email],
                context=email_context,
            )

        logger.info(f"Notification sent to user {user_id}: {title}")
        return True

    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {str(e)}")
        return False


@shared_task
def send_bulk_notification(
    user_ids, title, message, notification_type="info", email_notification=False
):
    """
    Send notification to multiple users.

    Args:
        user_ids: List of user IDs to notify
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        email_notification: Whether to also send email notifications
    """
    results = []
    for user_id in user_ids:
        result = send_notification.delay(
            user_id, title, message, notification_type, email_notification
        )
        results.append(result)

    logger.info(f"Bulk notification sent to {len(user_ids)} users: {title}")
    return results
