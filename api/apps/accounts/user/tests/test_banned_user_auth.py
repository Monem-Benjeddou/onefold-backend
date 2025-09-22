from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from apps.accounts.user.models import User


@override_settings(RATE_LIMITER_ENABLED=False)
class BannedUserAuthTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
        )

        self.regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="Password123",
            fullname="Regular User",
            role="user",
        )

        self.temp_banned_user = User.objects.create_user(
            username="tempbanneduser",
            email="tempbanned@example.com",
            password="Password123",
            fullname="Temp Banned User",
            role="user",
            is_banned=True,
            ban_reason="Temporary violation",
            banned_at=timezone.now(),
            banned_by=self.admin_user,
            ban_expires_at=timezone.now() + timedelta(hours=24),
        )

        self.perm_banned_user = User.objects.create_user(
            username="permbanneduser",
            email="permbanned@example.com",
            password="Password123",
            fullname="Permanently Banned User",
            role="user",
            is_banned=True,
            ban_reason="Serious violation",
            banned_at=timezone.now(),
            banned_by=self.admin_user,
        )

        self.expired_ban_user = User.objects.create_user(
            username="expiredbanneduser",
            email="expiredbanned@example.com",
            password="Password123",
            fullname="Expired Ban User",
            role="user",
            is_banned=True,
            ban_reason="Old violation",
            banned_at=timezone.now() - timedelta(hours=48),
            banned_by=self.admin_user,
            ban_expires_at=timezone.now() - timedelta(hours=24),
        )

    def test_regular_user_login_success(self):
        """Test that regular user can login successfully"""
        url = reverse("auth-login")
        data = {"email": "regular@example.com", "password": "Password123"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_temporarily_banned_user_login_forbidden(self):
        """Test that temporarily banned user cannot login"""
        url = reverse("auth-login")
        data = {"email": "tempbanned@example.com", "password": "Password123"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("temporarily banned", response.data["error"])
        self.assertIn("Temporary violation", response.data["error"])
        self.assertIn("Ban expires at:", response.data["error"])

    def test_permanently_banned_user_login_forbidden(self):
        """Test that permanently banned user cannot login"""
        url = reverse("auth-login")
        data = {"email": "permbanned@example.com", "password": "Password123"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("temporarily banned", response.data["error"])
        self.assertIn("Serious violation", response.data["error"])
        self.assertIn("permanent ban", response.data["error"])

    def test_expired_ban_user_login_success(self):
        """Test that user with expired ban can login successfully"""
        url = reverse("auth-login")
        data = {"email": "expiredbanned@example.com", "password": "Password123"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_is_currently_banned_method_temp_ban(self):
        """Test is_currently_banned method for temporarily banned user"""
        self.assertTrue(self.temp_banned_user.is_currently_banned())

    def test_is_currently_banned_method_perm_ban(self):
        """Test is_currently_banned method for permanently banned user"""
        self.assertTrue(self.perm_banned_user.is_currently_banned())

    def test_is_currently_banned_method_expired_ban(self):
        """Test is_currently_banned method for user with expired ban"""
        self.assertFalse(self.expired_ban_user.is_currently_banned())

    def test_is_currently_banned_method_not_banned(self):
        """Test is_currently_banned method for regular user"""
        self.assertFalse(self.regular_user.is_currently_banned())

    def test_user_serializer_includes_ban_fields(self):
        """Test that user serializer includes ban-related fields"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("retrieve-user", kwargs={"pk": self.temp_banned_user.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data

        self.assertIn("is_banned", user_data)
        self.assertIn("is_currently_banned", user_data)
        self.assertIn("ban_reason", user_data)
        self.assertIn("banned_at", user_data)
        self.assertIn("banned_by_username", user_data)
        self.assertIn("ban_expires_at", user_data)

        self.assertTrue(user_data["is_banned"])
        self.assertTrue(user_data["is_currently_banned"])
        self.assertEqual(user_data["ban_reason"], "Temporary violation")
        self.assertEqual(user_data["banned_by_username"], self.admin_user.username)
        self.assertIsNotNone(user_data["banned_at"])
        self.assertIsNotNone(user_data["ban_expires_at"])

    def test_user_serializer_not_banned_user(self):
        """Test user serializer for non-banned user"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("retrieve-user", kwargs={"pk": self.regular_user.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data

        self.assertFalse(user_data["is_banned"])
        self.assertFalse(user_data["is_currently_banned"])
        self.assertIsNone(user_data["ban_reason"])
        self.assertIsNone(user_data["banned_at"])
        self.assertIsNone(user_data["banned_by_username"])
        self.assertIsNone(user_data["ban_expires_at"])
