from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from apps.accounts.user.models import User


@override_settings(RATE_LIMITER_ENABLED=False)
class BanUserViewTest(TestCase):
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

        self.target_superuser = User.objects.create_user(
            username="targetsuperuser",
            email="targetsuperuser@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

    def test_ban_user_as_admin_success(self):
        """Test that admin can ban regular user successfully"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-ban-user", kwargs={"pk": self.regular_user.pk})

        data = {"reason": "Violation of terms", "duration_hours": 24}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_banned)
        self.assertEqual(self.regular_user.ban_reason, "Violation of terms")
        self.assertEqual(self.regular_user.banned_by, self.admin_user)
        self.assertIsNotNone(self.regular_user.banned_at)
        self.assertIsNotNone(self.regular_user.ban_expires_at)

    def test_ban_user_permanent_ban(self):
        """Test permanent ban (no duration specified)"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-ban-user", kwargs={"pk": self.regular_user.pk})

        data = {"reason": "Serious violation"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_banned)
        self.assertIsNone(self.regular_user.ban_expires_at)
        self.assertTrue(response.data["is_permanent"])

    def test_ban_user_without_reason(self):
        """Test banning user without providing reason"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-ban-user", kwargs={"pk": self.regular_user.pk})

        data = {"duration_hours": 12}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_banned)
        self.assertEqual(self.regular_user.ban_reason, "")

    def test_ban_user_unauthenticated(self):
        """Test that unauthenticated users cannot ban"""
        url = reverse("admin-ban-user", kwargs={"pk": self.regular_user.pk})

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ban_user_as_regular_user_forbidden(self):
        """Test that regular users cannot ban other users"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("admin-ban-user", kwargs={"pk": self.admin_user.pk})

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ban_superuser_as_admin_forbidden(self):
        """Test that admin cannot ban superuser"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-ban-user", kwargs={"pk": self.target_superuser.pk})

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Cannot ban superuser accounts", response.data["detail"])

    def test_ban_superuser_as_superuser_success(self):
        """Test that superuser can ban another superuser"""
        self.client.force_authenticate(user=self.superuser)
        url = reverse("admin-ban-user", kwargs={"pk": self.target_superuser.pk})

        data = {"reason": "Admin misconduct", "duration_hours": 48}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_superuser.refresh_from_db()
        self.assertTrue(self.target_superuser.is_banned)

    def test_ban_own_account_forbidden(self):
        """Test that users cannot ban their own account"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-ban-user", kwargs={"pk": self.admin_user.pk})

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot ban your own account", response.data["detail"])

    def test_ban_already_banned_user(self):
        """Test banning a user who is already banned"""

        self.regular_user.is_banned = True
        self.regular_user.banned_at = timezone.now()
        self.regular_user.save()

        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-ban-user", kwargs={"pk": self.regular_user.pk})

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User is already banned", response.data["detail"])

    def test_ban_user_invalid_duration(self):
        """Test banning user with invalid duration"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-ban-user", kwargs={"pk": self.regular_user.pk})

        data = {"duration_hours": -5}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("error", response.data)
        self.assertIn("duration_hours", response.data["error"])
        self.assertIn(
            "Ensure this value is greater than or equal to 1",
            str(response.data["error"]["duration_hours"]),
        )

    def test_ban_user_invalid_duration_format(self):
        """Test banning user with invalid duration format"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-ban-user", kwargs={"pk": self.regular_user.pk})

        data = {"duration_hours": "invalid"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("error", response.data)
        self.assertIn("duration_hours", response.data["error"])
        self.assertIn("valid integer", str(response.data["error"]["duration_hours"]))

    def test_ban_nonexistent_user(self):
        """Test banning non-existent user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "admin-ban-user", kwargs={"pk": "00000000-0000-0000-0000-000000000000"}
        )

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ban_user_with_put_method(self):
        """Test that PUT method works for banning users"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-ban-user", kwargs={"pk": self.regular_user.pk})

        data = {"reason": "PUT method test", "duration_hours": 12}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_banned)
        self.assertEqual(self.regular_user.ban_reason, "PUT method test")
