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
class UpdateUserRateLimitTest(TestCase):
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
            fullname="Test User Original",
            role="user",
        )

        self.url = reverse("update-user", kwargs={"pk": self.user_to_update.pk})

        self.client.force_authenticate(user=self.admin_user)

        self.valid_data_template = {
            "username": "updateduser",
            "email": "updated@example.com",
            "fullname": "Updated User",
            "role": "user",
        }

        cache.clear()

    def tearDown(self):

        cache.clear()

    def test_update_user_rate_limit(self):
        """Test that update user endpoint is rate limited"""

        for i in range(10):
            data = self.valid_data_template.copy()
            data["username"] = f"updateduser{i}"
            data["email"] = f"updated{i}@example.com"
            data["fullname"] = f"Updated User {i}"

            response = self.client.put(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.user_to_update.refresh_from_db()

        data = self.valid_data_template.copy()
        data["username"] = "ratelimiteduser"
        data["email"] = "ratelimited@example.com"
        data["fullname"] = "Rate Limited User"

        response = self.client.put(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.json().get("detail"), "Rate limit exceeded")

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_update_user_without_rate_limit(self):
        """Test that update user endpoint works without rate limiting when disabled"""

        for i in range(15):
            data = self.valid_data_template.copy()
            data["username"] = f"nolimituser{i}"
            data["email"] = f"nolimit{i}@example.com"
            data["fullname"] = f"No Limit User {i}"

            response = self.client.put(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.user_to_update.refresh_from_db()
