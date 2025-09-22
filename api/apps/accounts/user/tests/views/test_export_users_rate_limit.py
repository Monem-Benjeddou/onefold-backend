from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache

from apps.accounts.user.models import User


@override_settings(
    RATE_LIMITER_ENABLED=True, _RATE_LIMIT_FORCE_ENABLED=True, TESTING=True
)
class ExportUsersRateLimitTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("export-users")

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

        for i in range(5):
            User.objects.create_user(
                username=f"testuser{i}",
                email=f"user{i}@example.com",
                password="Password123",
                fullname=f"Test User {i}",
                role="user",
            )

        self.client.force_authenticate(user=self.admin_user)

        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_export_users_json_rate_limit(self):
        """Test that export users endpoint is rate limited"""

        for i in range(3):
            response = self.client.get(self.url, {"format": "json"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.url, {"format": "json"})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.json().get("detail"), "Rate limit exceeded")

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_export_users_json_without_rate_limit(self):
        """Test that export users endpoint works without rate limiting when disabled"""

        for i in range(8):
            response = self.client.get(self.url, {"format": "json"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
