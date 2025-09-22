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
class CreateUserRateLimitTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("create-user")

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

        self.valid_data_template = {
            "fullname": "New Test User",
            "role": "user",
        }

        cache.clear()

    def tearDown(self):

        cache.clear()

    def test_create_user_rate_limit(self):
        """Test that create user endpoint is rate limited"""

        for i in range(5):
            data = self.valid_data_template.copy()
            data["email"] = f"user{i}@example.com"
            data["fullname"] = f"Test User {i}"

            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = self.valid_data_template.copy()
        data["email"] = "ratelimituser@example.com"
        data["fullname"] = "Rate Limited User"

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_create_user_without_rate_limit(self):
        """Test that create user endpoint works without rate limiting when disabled"""

        for i in range(10):
            data = self.valid_data_template.copy()
            data["email"] = f"nolimituser{i}@example.com"
            data["fullname"] = f"No Limit User {i}"

            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
