"""
Tests for NotificationDetailSerializer.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationDetailSerializer
from apps.notifications.tests.constants import (
    NOTIFICATION_STATUS_READ,
    NOTIFICATION_STATUS_UNREAD,
)

User = get_user_model()


class NotificationDetailSerializerTestCase(TestCase):
    """Test cases for NotificationDetailSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        self.notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            body="Test notification body",
            status=NOTIFICATION_STATUS_UNREAD,
        )

        self.factory = APIRequestFactory()
        self.request = self.factory.get(
            f"/api/v1/notifications/{self.notification.id}/"
        )
        self.request.user = self.user

    def test_serializer_fields(self):
        """Test that serializer contains expected fields."""
        serializer = NotificationDetailSerializer(
            instance=self.notification, context={"request": self.request}
        )

        expected_fields = [
            "id",
            "user",
            "title",
            "body",
            "status",
            "created",
            "updated",
        ]
        self.assertEqual(set(serializer.data.keys()), set(expected_fields))

    def test_serializer_read_only_fields(self):
        """Test that most fields are read-only."""
        serializer = NotificationDetailSerializer()
        expected_read_only_fields = [
            "id",
            "user",
            "title",
            "body",
            "created",
            "updated",
        ]

        for field in expected_read_only_fields:
            self.assertIn(field, serializer.Meta.read_only_fields)

    def test_status_field_editable(self):
        """Test that status field is editable (not in read_only_fields)."""
        serializer = NotificationDetailSerializer()
        self.assertNotIn("status", serializer.Meta.read_only_fields)

    def test_serializer_data_content(self):
        """Test that serializer returns correct data."""
        serializer = NotificationDetailSerializer(
            instance=self.notification, context={"request": self.request}
        )

        data = serializer.data

        self.assertEqual(data["id"], self.notification.id)
        self.assertEqual(data["user"], self.notification.user.id)
        self.assertEqual(data["title"], self.notification.title)
        self.assertEqual(data["body"], self.notification.body)
        self.assertEqual(data["status"], self.notification.status)
        self.assertIsNotNone(data["created"])
        self.assertIsNotNone(data["updated"])

    def test_status_field_update(self):
        """Test that status field can be updated."""
        data = {"status": NOTIFICATION_STATUS_READ}

        serializer = NotificationDetailSerializer(
            instance=self.notification,
            data=data,
            partial=True,
            context={"request": self.request},
        )

        self.assertTrue(serializer.is_valid())
        updated_notification = serializer.save()

        self.assertEqual(updated_notification.status, NOTIFICATION_STATUS_READ)

    def test_invalid_status_update(self):
        """Test that invalid status values are rejected."""
        data = {"status": "invalid_status"}

        serializer = NotificationDetailSerializer(
            instance=self.notification,
            data=data,
            partial=True,
            context={"request": self.request},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)

    def test_read_only_field_updates_ignored(self):
        """Test that read-only fields cannot be updated."""
        original_title = self.notification.title
        original_body = self.notification.body

        data = {
            "title": "New Title",
            "body": "New Body",
            "status": NOTIFICATION_STATUS_READ,
        }

        serializer = NotificationDetailSerializer(
            instance=self.notification,
            data=data,
            partial=True,
            context={"request": self.request},
        )

        self.assertTrue(serializer.is_valid())
        updated_notification = serializer.save()

        self.assertEqual(updated_notification.status, NOTIFICATION_STATUS_READ)

        self.assertEqual(updated_notification.title, original_title)
        self.assertEqual(updated_notification.body, original_body)

    def test_serializer_with_different_users(self):
        """Test serializer works with different user scenarios."""
        user2 = User.objects.create_user(
            email="user2@example.com", password="testpass123"
        )

        notification2 = Notification.objects.create(
            user=user2,
            title="User 2 Notification",
            body="Body for user 2",
            status=NOTIFICATION_STATUS_UNREAD,
        )

        serializer = NotificationDetailSerializer(
            instance=notification2, context={"request": self.request}
        )

        data = serializer.data
        self.assertEqual(data["user"], user2.id)
        self.assertEqual(data["title"], "User 2 Notification")

    def test_serializer_handles_null_fields(self):
        """Test serializer handles notifications with null optional fields."""
        notification_null = Notification.objects.create(
            user=self.user, title=None, body=None, status=NOTIFICATION_STATUS_UNREAD
        )

        serializer = NotificationDetailSerializer(
            instance=notification_null, context={"request": self.request}
        )

        data = serializer.data
        self.assertIsNone(data["title"])
        self.assertIsNone(data["body"])
        self.assertEqual(data["status"], NOTIFICATION_STATUS_UNREAD)

    def test_validation_with_empty_data(self):
        """Test validation with empty update data."""
        serializer = NotificationDetailSerializer(
            instance=self.notification,
            data={},
            partial=True,
            context={"request": self.request},
        )

        self.assertTrue(serializer.is_valid())

        updated_notification = serializer.save()
        self.assertEqual(updated_notification.status, self.notification.status)

    def test_full_update_vs_partial_update(self):
        """Test difference between full and partial updates."""

        partial_data = {"status": NOTIFICATION_STATUS_READ}
        partial_serializer = NotificationDetailSerializer(
            instance=self.notification,
            data=partial_data,
            partial=True,
            context={"request": self.request},
        )

        self.assertTrue(partial_serializer.is_valid())

        full_data = {"status": NOTIFICATION_STATUS_READ}
        full_serializer = NotificationDetailSerializer(
            instance=self.notification,
            data=full_data,
            partial=False,
            context={"request": self.request},
        )

        self.assertTrue(full_serializer.is_valid())
