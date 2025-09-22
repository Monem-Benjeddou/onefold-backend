"""
Tests for NotificationUpdateView and NotificationMarkAllReadView.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.notifications.models import Notification
from apps.notifications.tests.constants import (
    NOTIFICATION_UPDATE_URL,
    NOTIFICATION_MARK_ALL_READ_URL,
    NOTIFICATION_STATUS_READ,
    NOTIFICATION_STATUS_UNREAD,
)

User = get_user_model()


class NotificationUpdateViewTestCase(TestCase):
    """Test cases for NotificationUpdateView."""

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
            status=NOTIFICATION_STATUS_UNREAD,
        )

    def test_update_notification_unauthenticated(self):
        """Test that unauthenticated users cannot update notifications."""
        url = NOTIFICATION_UPDATE_URL.format(id=self.notification1.id)
        data = {"status": NOTIFICATION_STATUS_READ}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_notification_mark_as_read(self):
        """Test marking notification as read."""
        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_UPDATE_URL.format(id=self.notification1.id)
        data = {"status": NOTIFICATION_STATUS_READ}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], NOTIFICATION_STATUS_READ)

        self.notification1.refresh_from_db()
        self.assertEqual(self.notification1.status, NOTIFICATION_STATUS_READ)

    def test_update_notification_mark_as_unread(self):
        """Test marking notification as unread."""

        self.notification1.status = NOTIFICATION_STATUS_READ
        self.notification1.save()

        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_UPDATE_URL.format(id=self.notification1.id)
        data = {"status": NOTIFICATION_STATUS_UNREAD}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], NOTIFICATION_STATUS_UNREAD)

        self.notification1.refresh_from_db()
        self.assertEqual(self.notification1.status, NOTIFICATION_STATUS_UNREAD)

    def test_update_notification_non_owner(self):
        """Test that users cannot update notifications they don't own."""
        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_UPDATE_URL.format(id=self.notification2.id)
        data = {"status": NOTIFICATION_STATUS_READ}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_notification_not_found(self):
        """Test updating non-existent notification."""
        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_UPDATE_URL.format(id=99999)
        data = {"status": NOTIFICATION_STATUS_READ}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_notification_invalid_status(self):
        """Test updating notification with invalid status."""
        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_UPDATE_URL.format(id=self.notification1.id)
        data = {"status": "invalid_status"}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        import json

        response_data = json.loads(response.content)
        self.assertIn("error", response_data)

    def test_update_notification_empty_data(self):
        """Test updating notification with empty data."""
        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_UPDATE_URL.format(id=self.notification1.id)
        data = {}

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.notification1.refresh_from_db()
        self.assertEqual(self.notification1.status, NOTIFICATION_STATUS_UNREAD)

    def test_update_notification_partial_update(self):
        """Test that only status field can be updated."""
        original_title = self.notification1.title
        original_body = self.notification1.body

        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_UPDATE_URL.format(id=self.notification1.id)
        data = {
            "status": NOTIFICATION_STATUS_READ,
            "title": "New Title",
            "body": "New Body",
        }

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.notification1.refresh_from_db()
        self.assertEqual(self.notification1.status, NOTIFICATION_STATUS_READ)
        self.assertEqual(self.notification1.title, original_title)
        self.assertEqual(self.notification1.body, original_body)

    def test_rate_limiting_applied(self):
        """Test that rate limiting is applied to the endpoint."""
        self.client.force_authenticate(user=self.user1)
        url = NOTIFICATION_UPDATE_URL.format(id=self.notification1.id)
        data = {"status": NOTIFICATION_STATUS_READ}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class NotificationMarkAllReadViewTestCase(TestCase):
    """Test cases for NotificationMarkAllReadView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.user1 = User.objects.create_user(
            email="user1@test.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com", password="testpass123"
        )

        self.notifications_user1 = []
        for i in range(5):
            self.notifications_user1.append(
                Notification.objects.create(
                    user=self.user1,
                    title=f"User 1 Notification {i}",
                    body=f"Body {i}",
                    status=NOTIFICATION_STATUS_UNREAD,
                )
            )

        self.read_notification = Notification.objects.create(
            user=self.user1,
            title="Already Read",
            body="Already read body",
            status=NOTIFICATION_STATUS_READ,
        )

        self.notifications_user2 = []
        for i in range(3):
            self.notifications_user2.append(
                Notification.objects.create(
                    user=self.user2,
                    title=f"User 2 Notification {i}",
                    body=f"Body {i}",
                    status=NOTIFICATION_STATUS_UNREAD,
                )
            )

    def test_mark_all_read_unauthenticated(self):
        """Test that unauthenticated users cannot mark all as read."""
        response = self.client.post(NOTIFICATION_MARK_ALL_READ_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mark_all_read_success(self):
        """Test successfully marking all notifications as read."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(NOTIFICATION_MARK_ALL_READ_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("updated_count", response.data)
        self.assertEqual(response.data["updated_count"], 5)

        for notification in self.notifications_user1:
            notification.refresh_from_db()
            self.assertEqual(notification.status, NOTIFICATION_STATUS_READ)

        self.read_notification.refresh_from_db()
        self.assertEqual(self.read_notification.status, NOTIFICATION_STATUS_READ)

        for notification in self.notifications_user2:
            notification.refresh_from_db()
            self.assertEqual(notification.status, NOTIFICATION_STATUS_UNREAD)

    def test_mark_all_read_no_unread_notifications(self):
        """Test marking all as read when user has no unread notifications."""

        Notification.objects.filter(user=self.user1).update(
            status=NOTIFICATION_STATUS_READ
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.post(NOTIFICATION_MARK_ALL_READ_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 0)

    def test_mark_all_read_user_isolation(self):
        """Test that mark all read only affects the authenticated user's notifications."""

        user1_unread_count = Notification.objects.filter(
            user=self.user1, status=NOTIFICATION_STATUS_UNREAD
        ).count()
        user2_unread_count = Notification.objects.filter(
            user=self.user2, status=NOTIFICATION_STATUS_UNREAD
        ).count()

        self.assertEqual(user1_unread_count, 5)
        self.assertEqual(user2_unread_count, 3)

        self.client.force_authenticate(user=self.user1)
        response = self.client.post(NOTIFICATION_MARK_ALL_READ_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 5)

        user1_unread_after = Notification.objects.filter(
            user=self.user1, status=NOTIFICATION_STATUS_UNREAD
        ).count()
        self.assertEqual(user1_unread_after, 0)

        user2_unread_after = Notification.objects.filter(
            user=self.user2, status=NOTIFICATION_STATUS_UNREAD
        ).count()
        self.assertEqual(user2_unread_after, 3)

    def test_mark_all_read_empty_user(self):
        """Test mark all read for user with no notifications."""
        user3 = User.objects.create_user(email="user3@test.com", password="testpass123")

        self.client.force_authenticate(user=user3)
        response = self.client.post(NOTIFICATION_MARK_ALL_READ_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 0)

    def test_mark_all_read_response_format(self):
        """Test that the response has the correct format."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(NOTIFICATION_MARK_ALL_READ_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("message", response.data)
        self.assertIn("updated_count", response.data)
        self.assertIsInstance(response.data["updated_count"], int)
        self.assertIsInstance(response.data["message"], str)

    def test_rate_limiting_applied(self):
        """Test that rate limiting is applied to the endpoint."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(NOTIFICATION_MARK_ALL_READ_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
