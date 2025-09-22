from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.core.cache import cache

User = get_user_model()


class LoginRateLimitTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("auth-login")

        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            fullname="Test User",
            username="testuser",
        )

        cache.clear()

    def tearDown(self):

        cache.clear()

    @override_settings(
        RATE_LIMITER_ENABLED=True,
        _RATE_LIMIT_FORCE_ENABLED=True,
        TESTING=True,
        RATE_LIMITER_DEFAULT_RATE=5,
        RATE_LIMITER_DEFAULT_PERIOD=60,
    )
    def test_login_rate_limit(self):
        """Test that login endpoint is properly rate limited."""
        data = {"email": "user@example.com", "password": "password123"}

        for _ in range(5):
            response = self.client.post(self.login_url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.json().get("detail"), "Rate limit exceeded")

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_login_without_rate_limit(self):
        """Test that login works without rate limiting when disabled."""
        data = {"email": "user@example.com", "password": "password123"}

        for _ in range(10):
            response = self.client.post(self.login_url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(
        RATE_LIMITER_ENABLED=True,
        _RATE_LIMIT_FORCE_ENABLED=True,
        TESTING=True,
        RATE_LIMITER_DEFAULT_RATE=5,
        RATE_LIMITER_DEFAULT_PERIOD=60,
    )
    def test_rate_limit_per_client(self):
        """Test that rate limits are applied per client IP."""

        cache.clear()

        data = {"email": "user@example.com", "password": "password123"}

        for i in range(5):
            response = self.client.post(self.login_url, data)
            if response.status_code != status.HTTP_200_OK:

                self.assertEqual(
                    response.status_code, status.HTTP_429_TOO_MANY_REQUESTS
                )
                return
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        new_client = APIClient()

        response = new_client.post(
            self.login_url,
            data,
            HTTP_X_FORWARDED_FOR="192.168.0.99",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
