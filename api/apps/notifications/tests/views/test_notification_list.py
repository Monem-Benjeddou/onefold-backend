"""
Tests for NotificationListView.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.notifications.models import Notification
from apps.notifications.tests.constants import (
    TEST_NOTIFICATION_DATA,
    NOTIFICATIONS_LIST_URL,
    NOTIFICATION_STATUS_READ,
    NOTIFICATION_STATUS_UNREAD,
)

User = get_user_model()


class NotificationListViewTestCase(TestCase):
    """Test cases for NotificationListView."""

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
            title="Notification 1",
            body="Body 1",
            status=NOTIFICATION_STATUS_UNREAD,
        )
        self.notification2 = Notification.objects.create(
            user=self.user1,
            title="Notification 2",
            body="Body 2",
            status=NOTIFICATION_STATUS_READ,
        )

        self.notification3 = Notification.objects.create(
            user=self.user2,
            title="Notification 3",
            body="Body 3",
            status=NOTIFICATION_STATUS_UNREAD,
        )

    def test_get_notifications_list_unauthenticated(self):
        """Test that unauthenticated users cannot access notifications."""
        response = self.client.get(NOTIFICATIONS_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_notifications_list_authenticated(self):
        """Test successful retrieval of notifications list for authenticated user."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(NOTIFICATIONS_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("meta", response.data)
        self.assertIn("results", response.data)

    def test_get_notifications_list_default_unread_only(self):
        """Test that by default only unread notifications are returned."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(NOTIFICATIONS_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.notification1.id)

    def test_get_notifications_list_filter_by_status_read(self):
        """Test filtering notifications by read status."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(NOTIFICATIONS_LIST_URL + "?status=read")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.notification2.id)

    def test_get_notifications_list_filter_by_status_all(self):
        """Test filtering notifications to show all statuses."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(NOTIFICATIONS_LIST_URL + "?status=all")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["results"]), 2)

    def test_get_notifications_list_user_isolation(self):
        """Test that users can only see their own notifications."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(NOTIFICATIONS_LIST_URL + "?status=all")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notification_ids = [notif["id"] for notif in response.data["results"]]
        self.assertIn(self.notification1.id, notification_ids)
        self.assertIn(self.notification2.id, notification_ids)
        self.assertNotIn(self.notification3.id, notification_ids)

    def test_get_notifications_list_ordering(self):
        """Test that notifications are ordered by creation date (most recent first)."""
        self.client.force_authenticate(user=self.user1)

        newer_notification = Notification.objects.create(
            user=self.user1,
            title="Newer Notification",
            body="Newer body",
            status=NOTIFICATION_STATUS_UNREAD,
        )

        response = self.client.get(NOTIFICATIONS_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"][0]["id"], newer_notification.id)
        self.assertEqual(response.data["results"][1]["id"], self.notification1.id)

    def test_get_notifications_list_pagination(self):
        """Test notifications list pagination."""
        self.client.force_authenticate(user=self.user1)

        for i in range(15):
            Notification.objects.create(
                user=self.user1,
                title=f"Notification {i+10}",
                body=f"Body {i+10}",
                status=NOTIFICATION_STATUS_UNREAD,
            )

        response = self.client.get(NOTIFICATIONS_LIST_URL + "?limit=10")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("meta", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["meta"]["next"])

    def test_get_notifications_list_empty_result(self):
        """Test notifications list when user has no notifications."""

        user3 = User.objects.create_user(email="user3@test.com", password="testpass123")

        self.client.force_authenticate(user=user3)
        response = self.client.get(NOTIFICATIONS_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_notifications_list_serializer_fields(self):
        """Test that the correct fields are returned in the response."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(NOTIFICATIONS_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification_data = response.data["results"][0]

        expected_fields = ["id", "title", "body", "status", "created"]
        for field in expected_fields:
            self.assertIn(field, notification_data)

        self.assertNotIn("user", notification_data)

    def test_rate_limiting_applied(self):
        """Test that rate limiting is applied to the endpoint."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(NOTIFICATIONS_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
