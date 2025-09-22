from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from apps.accounts.user.models import User


@override_settings(RATE_LIMITER_ENABLED=False)
class UnbanUserViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
            is_superuser=False,
        )

        self.superuser = User.objects.create_user(
            username="superuser",
            email="superuser@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

        self.regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="Password123",
            fullname="Regular User",
            role="user",
        )

        self.banned_user = User.objects.create_user(
            username="banneduser",
            email="banned@example.com",
            password="Password123",
            fullname="Banned User",
            role="user",
            is_banned=True,
            ban_reason="Test ban",
            banned_at=timezone.now(),
            banned_by=self.admin_user,
            ban_expires_at=timezone.now() + timedelta(hours=24),
        )

        self.superuser_banned_user = User.objects.create_user(
            username="superbanneduser",
            email="superbanned@example.com",
            password="Password123",
            fullname="Super Banned User",
            role="user",
            is_banned=True,
            ban_reason="Serious violation",
            banned_at=timezone.now(),
            banned_by=self.superuser,
        )

    def test_unban_user_as_admin_success(self):
        """Test that admin can unban user successfully"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-unban-user", kwargs={"pk": self.banned_user.pk})

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.banned_user.refresh_from_db()
        self.assertFalse(self.banned_user.is_banned)
        self.assertIsNone(self.banned_user.ban_reason)
        self.assertIsNone(self.banned_user.banned_at)
        self.assertIsNone(self.banned_user.banned_by)
        self.assertIsNone(self.banned_user.ban_expires_at)

    def test_unban_user_as_superuser_success(self):
        """Test that superuser can unban any user"""
        self.client.force_authenticate(user=self.superuser)
        url = reverse("admin-unban-user", kwargs={"pk": self.superuser_banned_user.pk})

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.superuser_banned_user.refresh_from_db()
        self.assertFalse(self.superuser_banned_user.is_banned)

    def test_unban_user_unauthenticated(self):
        """Test that unauthenticated users cannot unban"""
        url = reverse("admin-unban-user", kwargs={"pk": self.banned_user.pk})

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unban_user_as_regular_user_forbidden(self):
        """Test that regular users cannot unban other users"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("admin-unban-user", kwargs={"pk": self.banned_user.pk})

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unban_user_banned_by_superuser_as_admin_forbidden(self):
        """Test that admin cannot unban user banned by superuser"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-unban-user", kwargs={"pk": self.superuser_banned_user.pk})

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(
            "Cannot unban users banned by superusers", response.data["detail"]
        )

    def test_unban_not_banned_user(self):
        """Test unbanning a user who is not banned"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-unban-user", kwargs={"pk": self.regular_user.pk})

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User is not banned", response.data["detail"])

    def test_unban_nonexistent_user(self):
        """Test unbanning non-existent user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "admin-unban-user", kwargs={"pk": "00000000-0000-0000-0000-000000000000"}
        )

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unban_response_format(self):
        """Test that unban response contains correct data"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-unban-user", kwargs={"pk": self.banned_user.pk})

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertIn("user_id", response.data)
        self.assertIn("is_banned", response.data)
        self.assertIn("unbanned_at", response.data)
        self.assertIn("unbanned_by", response.data)
        self.assertEqual(response.data["is_banned"], False)
        self.assertEqual(response.data["user_id"], str(self.banned_user.id))
        self.assertEqual(response.data["unbanned_by"], str(self.admin_user.id))

    def test_unban_user_with_put_method(self):
        """Test that PUT method works for unbanning users"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-unban-user", kwargs={"pk": self.banned_user.pk})

        response = self.client.put(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.banned_user.refresh_from_db()
        self.assertFalse(self.banned_user.is_banned)
        self.assertIsNone(self.banned_user.ban_reason)
