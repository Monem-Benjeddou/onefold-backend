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
class UpdateRoleRateLimitTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_group, _ = Group.objects.get_or_create(name="Admin")

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
        )

        self.admin_user.groups.add(self.admin_group)

        self.user_to_update = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Password123",
            role="user",
        )

        self.url = reverse("update-role", kwargs={"pk": self.user_to_update.pk})

        self.client.force_authenticate(user=self.admin_user)

        self.valid_data_template = {
            "role": "moderator",
        }

        cache.clear()

    def tearDown(self):

        cache.clear()

    def test_update_role_rate_limit(self):
        """Test that update role endpoint is rate limited"""

        for i in range(10):
            data = self.valid_data_template.copy()

            data["role"] = "moderator" if i % 2 == 0 else "user"

            response = self.client.patch(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.user_to_update.refresh_from_db()

        data = self.valid_data_template.copy()
        data["role"] = "admin"

        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.json().get("detail"), "Rate limit exceeded")

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_update_role_without_rate_limit(self):
        """Test that update role endpoint works without rate limiting when disabled"""

        for i in range(15):
            data = self.valid_data_template.copy()

            data["role"] = "moderator" if i % 2 == 0 else "user"

            response = self.client.patch(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.user_to_update.refresh_from_db()
