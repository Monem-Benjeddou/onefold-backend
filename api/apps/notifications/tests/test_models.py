"""
Tests for Notification model.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.notifications.models import Notification
from apps.notifications.tests.constants import (
    NOTIFICATION_STATUS_READ,
    NOTIFICATION_STATUS_UNREAD,
)

User = get_user_model()


class NotificationModelTestCase(TestCase):
    """Test cases for Notification model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

    def test_notification_creation(self):
        """Test basic notification creation."""
        notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            body="Test body",
            status=NOTIFICATION_STATUS_UNREAD,
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.body, "Test body")
        self.assertEqual(notification.status, NOTIFICATION_STATUS_UNREAD)
        self.assertIsNotNone(notification.created)
        self.assertIsNotNone(notification.updated)

    def test_notification_default_status(self):
        """Test that default status is unread."""
        notification = Notification.objects.create(
            user=self.user, title="Test Notification", body="Test body"
        )

        self.assertEqual(notification.status, NOTIFICATION_STATUS_UNREAD)

    def test_notification_with_null_fields(self):
        """Test notification creation with null optional fields."""
        notification = Notification.objects.create(
            user=self.user, title=None, body=None, status=NOTIFICATION_STATUS_UNREAD
        )

        self.assertEqual(notification.user, self.user)
        self.assertIsNone(notification.title)
        self.assertIsNone(notification.body)
        self.assertEqual(notification.status, NOTIFICATION_STATUS_UNREAD)

    def test_notification_with_empty_fields(self):
        """Test notification creation with empty optional fields."""
        notification = Notification.objects.create(
            user=self.user, title="", body="", status=NOTIFICATION_STATUS_READ
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, "")
        self.assertEqual(notification.body, "")
        self.assertEqual(notification.status, NOTIFICATION_STATUS_READ)

    def test_notification_without_user(self):
        """Test notification creation without user (should be allowed)."""
        notification = Notification.objects.create(
            user=None,
            title="System Notification",
            body="System message",
            status=NOTIFICATION_STATUS_UNREAD,
        )

        self.assertIsNone(notification.user)
        self.assertEqual(notification.title, "System Notification")

    def test_notification_status_choices(self):
        """Test that only valid status choices are accepted."""

        notification_read = Notification.objects.create(
            user=self.user, title="Read Notification", status=NOTIFICATION_STATUS_READ
        )
        self.assertEqual(notification_read.status, NOTIFICATION_STATUS_READ)

        notification_unread = Notification.objects.create(
            user=self.user,
            title="Unread Notification",
            status=NOTIFICATION_STATUS_UNREAD,
        )
        self.assertEqual(notification_unread.status, NOTIFICATION_STATUS_UNREAD)

    def test_notification_string_representation(self):
        """Test notification string representation."""
        notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            body="Test body",
            status=NOTIFICATION_STATUS_UNREAD,
        )

        str_repr = str(notification)
        self.assertIn("Notification", str_repr)

    def test_notification_max_length_fields(self):
        """Test notification with maximum length fields."""
        long_title = "A" * 250
        long_body = "B" * 1000

        notification = Notification.objects.create(
            user=self.user,
            title=long_title,
            body=long_body,
            status=NOTIFICATION_STATUS_UNREAD,
        )

        self.assertEqual(notification.title, long_title)
        self.assertEqual(notification.body, long_body)

    def test_notification_title_exceeds_max_length(self):
        """Test that title exceeding max length is handled gracefully."""
        long_title = "A" * 251

        notification = Notification.objects.create(
            user=self.user,
            title=long_title,
            body="Test body",
            status=NOTIFICATION_STATUS_UNREAD,
        )

        self.assertIsNotNone(notification.id)

    def test_notification_status_constants(self):
        """Test that status constants are correctly defined."""
        self.assertEqual(Notification.MARKED_READ, "r")
        self.assertEqual(Notification.MARKED_UNREAD, "u")

        choices_dict = dict(Notification.CHOICES)
        self.assertEqual(choices_dict["r"], "read")
        self.assertEqual(choices_dict["u"], "unread")

    def test_notification_related_name(self):
        """Test that related name works correctly."""
        notification1 = Notification.objects.create(
            user=self.user, title="Notification 1", status=NOTIFICATION_STATUS_UNREAD
        )
        notification2 = Notification.objects.create(
            user=self.user, title="Notification 2", status=NOTIFICATION_STATUS_READ
        )

        user_notifications = self.user.notifications.all()
        self.assertEqual(user_notifications.count(), 2)
        self.assertIn(notification1, user_notifications)
        self.assertIn(notification2, user_notifications)

    def test_notification_cascade_delete(self):
        """Test that notifications are deleted when user is deleted."""
        notification = Notification.objects.create(
            user=self.user, title="Test Notification", status=NOTIFICATION_STATUS_UNREAD
        )

        notification_id = notification.id
        self.assertTrue(Notification.objects.filter(id=notification_id).exists())

        self.user.delete()

        self.assertFalse(Notification.objects.filter(id=notification_id).exists())

    def test_notification_timestamps(self):
        """Test that created and updated timestamps work correctly."""
        notification = Notification.objects.create(
            user=self.user, title="Test Notification", status=NOTIFICATION_STATUS_UNREAD
        )

        original_created = notification.created
        original_updated = notification.updated

        notification.status = NOTIFICATION_STATUS_READ
        notification.save()

        notification.refresh_from_db()

        self.assertEqual(notification.created, original_created)
        self.assertGreater(notification.updated, original_updated)

    def test_notification_filtering_by_status(self):
        """Test filtering notifications by status."""

        read_notification = Notification.objects.create(
            user=self.user, title="Read Notification", status=NOTIFICATION_STATUS_READ
        )
        unread_notification = Notification.objects.create(
            user=self.user,
            title="Unread Notification",
            status=NOTIFICATION_STATUS_UNREAD,
        )

        read_notifications = Notification.objects.filter(
            status=NOTIFICATION_STATUS_READ
        )
        unread_notifications = Notification.objects.filter(
            status=NOTIFICATION_STATUS_UNREAD
        )

        self.assertIn(read_notification, read_notifications)
        self.assertNotIn(unread_notification, read_notifications)

        self.assertIn(unread_notification, unread_notifications)
        self.assertNotIn(read_notification, unread_notifications)

    def test_notification_ordering(self):
        """Test notification ordering by creation date."""

        notification1 = Notification.objects.create(
            user=self.user,
            title="First Notification",
            status=NOTIFICATION_STATUS_UNREAD,
        )

        notification2 = Notification.objects.create(
            user=self.user,
            title="Second Notification",
            status=NOTIFICATION_STATUS_UNREAD,
        )

        notifications = Notification.objects.filter(user=self.user).order_by("-created")
        notifications_list = list(notifications)

        self.assertEqual(notifications_list[0], notification2)
        self.assertEqual(notifications_list[1], notification1)
