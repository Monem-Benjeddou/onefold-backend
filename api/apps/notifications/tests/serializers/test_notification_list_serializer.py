"""
Tests for NotificationListSerializer.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationListSerializer
from apps.notifications.tests.constants import (
    NOTIFICATION_STATUS_READ,
    NOTIFICATION_STATUS_UNREAD,
)

User = get_user_model()


class NotificationListSerializerTestCase(TestCase):
    """Test cases for NotificationListSerializer."""

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
        self.request = self.factory.get("/api/v1/notifications/")
        self.request.user = self.user

    def test_serializer_fields(self):
        """Test that serializer contains expected fields."""
        serializer = NotificationListSerializer(
            instance=self.notification, context={"request": self.request}
        )

        expected_fields = ["id", "title", "body", "status", "created"]
        self.assertEqual(set(serializer.data.keys()), set(expected_fields))

    def test_serializer_read_only_fields(self):
        """Test that all fields are read-only."""
        serializer = NotificationListSerializer()
        expected_read_only_fields = ["id", "title", "body", "status", "created"]

        for field in expected_read_only_fields:
            self.assertIn(field, serializer.Meta.read_only_fields)

    def test_serializer_data_content(self):
        """Test that serializer returns correct data."""
        serializer = NotificationListSerializer(
            instance=self.notification, context={"request": self.request}
        )

        data = serializer.data

        self.assertEqual(data["id"], self.notification.id)
        self.assertEqual(data["title"], self.notification.title)
        self.assertEqual(data["body"], self.notification.body)
        self.assertEqual(data["status"], self.notification.status)
        self.assertIsNotNone(data["created"])

    def test_serializer_user_not_exposed(self):
        """Test that user field is not exposed in serialized data."""
        serializer = NotificationListSerializer(
            instance=self.notification, context={"request": self.request}
        )

        self.assertNotIn("user", serializer.data)

    def test_serializer_validation_with_request_context(self):
        """Test that validation works with request context."""
        data = {
            "title": "New Notification",
            "body": "New body",
            "status": NOTIFICATION_STATUS_UNREAD,
        }

        serializer = NotificationListSerializer(
            data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validate(data)
        self.assertEqual(validated_data["user"], self.user)

    def test_serializer_validation_without_request_context(self):
        """Test that validation works without request context."""
        data = {
            "title": "New Notification",
            "body": "New body",
            "status": NOTIFICATION_STATUS_UNREAD,
        }

        serializer = NotificationListSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validate(data)

        self.assertNotIn("user", validated_data)

    def test_multiple_notifications_serialization(self):
        """Test serialization of multiple notifications."""

        notification2 = Notification.objects.create(
            user=self.user,
            title="Second Notification",
            body="Second body",
            status=NOTIFICATION_STATUS_READ,
        )

        notification3 = Notification.objects.create(
            user=self.user,
            title="Third Notification",
            body="Third body",
            status=NOTIFICATION_STATUS_UNREAD,
        )

        notifications = [self.notification, notification2, notification3]
        serializer = NotificationListSerializer(
            notifications, many=True, context={"request": self.request}
        )

        self.assertEqual(len(serializer.data), 3)

        for notification_data in serializer.data:
            expected_fields = ["id", "title", "body", "status", "created"]
            self.assertEqual(set(notification_data.keys()), set(expected_fields))

    def test_serializer_handles_empty_fields(self):
        """Test serializer handles notifications with empty optional fields."""
        notification_empty = Notification.objects.create(
            user=self.user, title="", body=None, status=NOTIFICATION_STATUS_UNREAD
        )

        serializer = NotificationListSerializer(
            instance=notification_empty, context={"request": self.request}
        )

        data = serializer.data
        self.assertEqual(data["title"], "")
        self.assertIsNone(data["body"])
        self.assertEqual(data["status"], NOTIFICATION_STATUS_UNREAD)

    def test_status_field_values(self):
        """Test that status field contains valid values."""

        serializer_unread = NotificationListSerializer(
            instance=self.notification, context={"request": self.request}
        )
        self.assertEqual(serializer_unread.data["status"], NOTIFICATION_STATUS_UNREAD)

        read_notification = Notification.objects.create(
            user=self.user,
            title="Read Notification",
            body="Read body",
            status=NOTIFICATION_STATUS_READ,
        )

        serializer_read = NotificationListSerializer(
            instance=read_notification, context={"request": self.request}
        )
        self.assertEqual(serializer_read.data["status"], NOTIFICATION_STATUS_READ)
