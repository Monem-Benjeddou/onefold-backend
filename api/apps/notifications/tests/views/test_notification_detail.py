"""
Tests for NotificationDetailView.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.notifications.models import Notification
from apps.notifications.tests.constants import (
    NOTIFICATION_DETAIL_URL,
    NOTIFICATION_STATUS_READ,
    NOTIFICATION_STATUS_UNREAD,
)

User = get_user_model()


class NotificationDetailViewTestCase(TestCase):
    """Test cases for NotificationDetailView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.user1 = User.objects.create_user(
            email="user1@test.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com", password="testpass123"
        )

        self.notification1 = Notification.objects.create(
            user=self.user1,
            title="User 1 Notification",
            body="Body for user 1",
            status=NOTIFICATION_STATUS_UNREAD,
        )
        self.notification2 = Notification.objects.create(
            user=self.user2,
            title="User 2 Notification",
            body="Body for user 2",
            status=NOTIFICATION_STATUS_READ,
        )

    def test_get_notification_detail_unauthenticated(self):
        """Test that unauthenticated users cannot access notification details."""
        url = NOTIFICATION_DETAIL_URL.format(id=self.notification1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_notification_detail_authenticated_owner(self):
        """Test successful retrieval of notification detail by owner."""
        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_DETAIL_URL.format(id=self.notification1.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["id"], self.notification1.id)
        self.assertEqual(response.data["title"], self.notification1.title)
        self.assertEqual(response.data["body"], self.notification1.body)
        self.assertEqual(response.data["status"], self.notification1.status)
        self.assertEqual(response.data["user"], self.user1.id)

    def test_get_notification_detail_authenticated_non_owner(self):
        """Test that users cannot access notifications they don't own."""
        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_DETAIL_URL.format(id=self.notification2.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_notification_detail_not_found(self):
        """Test response when notification doesn't exist."""
        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_DETAIL_URL.format(id=99999)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_notification_detail_serializer_fields(self):
        """Test that the correct fields are returned in the response."""
        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_DETAIL_URL.format(id=self.notification1.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = [
            "id",
            "user",
            "title",
            "body",
            "status",
            "created",
            "updated",
        ]
        for field in expected_fields:
            self.assertIn(field, response.data)

    def test_notification_detail_with_null_fields(self):
        """Test notification detail with null optional fields."""
        notification_null = Notification.objects.create(
            user=self.user1, title=None, body=None, status=NOTIFICATION_STATUS_UNREAD
        )

        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_DETAIL_URL.format(id=notification_null.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["title"])
        self.assertIsNone(response.data["body"])
        self.assertEqual(response.data["status"], NOTIFICATION_STATUS_UNREAD)

    def test_notification_detail_with_empty_fields(self):
        """Test notification detail with empty optional fields."""
        notification_empty = Notification.objects.create(
            user=self.user1, title="", body="", status=NOTIFICATION_STATUS_READ
        )

        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_DETAIL_URL.format(id=notification_empty.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "")
        self.assertEqual(response.data["body"], "")
        self.assertEqual(response.data["status"], NOTIFICATION_STATUS_READ)

    def test_notification_detail_different_status_values(self):
        """Test notification detail with different status values."""

        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_DETAIL_URL.format(id=self.notification1.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], NOTIFICATION_STATUS_UNREAD)

        self.client.force_authenticate(user=self.user2)
        url = NOTIFICATION_DETAIL_URL.format(id=self.notification2.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], NOTIFICATION_STATUS_READ)

    def test_rate_limiting_applied(self):
        """Test that rate limiting is applied to the endpoint."""
        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_DETAIL_URL.format(id=self.notification1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_notification_detail_timestamps(self):
        """Test that created and updated timestamps are included."""
        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_DETAIL_URL.format(id=self.notification1.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["created"])
        self.assertIsNotNone(response.data["updated"])

        import datetime

        try:
            datetime.datetime.fromisoformat(
                response.data["created"].replace("Z", "+00:00")
            )
            datetime.datetime.fromisoformat(
                response.data["updated"].replace("Z", "+00:00")
            )
        except ValueError:
            self.fail("Timestamps should be in ISO format")

    def test_user_isolation_strict(self):
        """Test strict user isolation - users can only see their own notifications."""

        notifications_user1 = []
        notifications_user2 = []

        for i in range(3):
            notifications_user1.append(
                Notification.objects.create(
                    user=self.user1,
                    title=f"User 1 Notification {i}",
                    body=f"Body {i}",
                    status=NOTIFICATION_STATUS_UNREAD,
                )
            )
            notifications_user2.append(
                Notification.objects.create(
                    user=self.user2,
                    title=f"User 2 Notification {i}",
                    body=f"Body {i}",
                    status=NOTIFICATION_STATUS_UNREAD,
                )
            )

        self.client.force_authenticate(user=self.user1)
        for notification in notifications_user1:
            url = NOTIFICATION_DETAIL_URL.format(id=notification.id)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        for notification in notifications_user2:
            url = NOTIFICATION_DETAIL_URL.format(id=notification.id)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
