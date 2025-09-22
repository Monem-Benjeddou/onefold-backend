from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache
from django.contrib.auth.models import Group

from apps.accounts.user.models import User


@override_settings(
    RATE_LIMITER_ENABLED=True, _RATE_LIMIT_FORCE_ENABLED=True, TESTING=True
)
class ListUsersRateLimitTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("list-user")

        self.admin_group, _ = Group.objects.get_or_create(name="Admin")

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
        )

        self.admin_user.groups.add(self.admin_group)

        self.client.force_authenticate(user=self.admin_user)

        cache.clear()

    def tearDown(self):

        cache.clear()

    def test_list_users_rate_limit(self):
        """Test that list users endpoint is rate limited"""

        for i in range(20):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.json().get("detail"), "Rate limit exceeded")

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_list_users_without_rate_limit(self):
        """Test that list users endpoint works without rate limiting when disabled"""

        for i in range(30):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
