from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache

from apps.accounts.user.models import User


@override_settings(
    RATE_LIMITER_ENABLED=True, _RATE_LIMIT_FORCE_ENABLED=True, TESTING=True
)
class DeleteUserRateLimitTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

        self.client.force_authenticate(user=self.admin_user)

        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_delete_user_rate_limit(self):
        """Test that delete user endpoint is rate limited"""

        for i in range(5):

            user_to_delete = User.objects.create_user(
                username=f"testuser{i}",
                email=f"testuser{i}@example.com",
                password="Password123",
                fullname=f"Test User {i}",
                role="user",
            )

            url = reverse("delete-user", kwargs={"pk": user_to_delete.pk})
            response = self.client.delete(url)
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        final_user = User.objects.create_user(
            username="finaluser",
            email="finaluser@example.com",
            password="Password123",
            fullname="Final User",
            role="user",
        )

        url = reverse("delete-user", kwargs={"pk": final_user.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @override_settings(RATE_LIMITER_ENABLED=False)
    def test_delete_user_without_rate_limit(self):
        """Test that delete user endpoint works without rate limiting when disabled"""

        for i in range(8):

            user_to_delete = User.objects.create_user(
                username=f"nolimit{i}",
                email=f"nolimit{i}@example.com",
                password="Password123",
                fullname=f"No Limit User {i}",
                role="user",
            )

            url = reverse("delete-user", kwargs={"pk": user_to_delete.pk})
            response = self.client.delete(url)
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
