from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache
import time


class RegisterRateLimitTestCase(TestCase):
    def setUp(self):

        cache.clear()

        self.client = APIClient()
        self.register_url = reverse("auth-register")

    def tearDown(self):

        cache.clear()

    @override_settings(
        RATE_LIMITER_ENABLED=True,
        _RATE_LIMIT_FORCE_ENABLED=True,
        TESTING=True,
        RATE_LIMITER_DEFAULT_RATE=3,
        RATE_LIMITER_DEFAULT_PERIOD=3600,
    )
    def test_register_rate_limit(self):
        """Test that register endpoint is properly rate limited."""

        cache.clear()

        client = APIClient()
        client.defaults["REMOTE_ADDR"] = "192.168.1.100"

        test_users = [
            {
                "email": f"ratelimit{i}@example.com",
                "password": "StrongPassword123!",
                "fullname": f"Rate Limit Test User {i}",
                "username": f"ratelimituser{i}",
                "phone_number": f"+123456789{i}",
            }
            for i in range(4)
        ]

        for i in range(3):
            response = client.post(self.register_url, test_users[i])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = client.post(self.register_url, test_users[3])
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.json().get("detail"), "Rate limit exceeded")

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_register_without_rate_limit(self):
        """Test that register works without rate limiting when disabled."""

        test_users = [
            {
                "email": f"noratelimit{i}@example.com",
                "password": "StrongPassword123!",
                "fullname": f"No Rate Limit Test User {i}",
                "username": f"noratelimituser{i}",
                "phone_number": f"+987654321{i}",
            }
            for i in range(5)
        ]

        for i in range(5):
            response = self.client.post(self.register_url, test_users[i])
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
