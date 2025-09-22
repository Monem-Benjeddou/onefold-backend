from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.user.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
import json
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.accounts.user.tests.factories import UserFactory

User = get_user_model()


@override_settings(
    RATE_LIMITER_ENABLED=True, _RATE_LIMIT_FORCE_ENABLED=True, TESTING=True
)
class UserViewsetsRateLimiterTests(TestCase):
    def setUp(self):
        """Set up test data and authenticate"""

        cache.clear()

        self.client = APIClient()

        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
            username="admin",
            is_staff=True,
        )
        self.admin.role = "admin"
        self.admin.save()

        self.user = User.objects.create_user(
            email="user@example.com",
            password="userpass123",
            username="testuser",
            fullname="Test User",
        )

        self.client.force_authenticate(user=self.admin)

    def tearDown(self):
        cache.clear()

    def test_create_user_rate_limit(self):
        """Test rate limiting for user creation"""
        url = reverse("create-user")

        for i in range(5):
            data = {
                "email": f"user{i}@example.com",
                "fullname": f"User {i}",
                "role": "user",
            }
            response = self.client.post(url, data)
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                f"Failed on request {i+1} with response: {response.content}",
            )

        data = {
            "email": "ratelimituser@example.com",
            "fullname": "Rate Limited User",
            "role": "user",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.json().get("detail"), "Rate limit exceeded")

    def test_update_user_rate_limit(self):
        """Test rate limiting for user updates with the new UpdateUserView (limit: 10/minute)"""
        url = reverse("update-user", kwargs={"pk": self.user.pk})

        for i in range(10):
            data = {"fullname": f"Updated Name {i}"}
            response = self.client.put(url, data)
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                f"Failed on request {i+1} with response: {response.content}",
            )

        data = {"fullname": "Rate Limited Update"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_list_users_rate_limit(self):
        """Test rate limiting for user listing with the new ListUsersView (limit: 20/minute)"""
        url = reverse("list-user")

        for i in range(20):
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                f"Failed on request {i+1} with response: {response.content}",
            )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_delete_user_rate_limit(self):
        """Test rate limiting for user deletion with the new DeleteUserView (limit: 5/minute)"""

        users = []
        for i in range(6):
            user = User.objects.create_user(
                email=f"delete{i}@example.com",
                password="testpass123",
                username=f"deleteuser{i}",
                fullname=f"Delete User {i}",
            )
            users.append(user)

        for i in range(5):
            url = reverse("delete-user", kwargs={"pk": users[i].pk})
            response = self.client.delete(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_204_NO_CONTENT,
                f"Failed on request {i+1} with response: {response.content}",
            )

        url = reverse("delete-user", kwargs={"pk": users[5].pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_update_role_rate_limit(self):
        """Test rate limiting for role updates with the new UpdateRoleView (limit: 10/minute)"""
        url = reverse("update-role", kwargs={"pk": self.user.pk})

        roles = ["user", "admin", "moderator"]

        for i in range(10):
            data = {"role": roles[i % 3]}
            response = self.client.patch(url, data)
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                f"Failed on request {i+1} with response: {response.content}",
            )

        data = {"role": "user"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @override_settings(RATE_LIMITER_ENABLED=False, _RATE_LIMIT_FORCE_ENABLED=False)
    def test_rate_limiter_disabled(self):
        """Test that rate limiting is bypassed when disabled"""

        url = reverse("create-user")
        for i in range(10):
            data = {
                "email": f"test{i}@example.com",
                "password": "testpass123",
                "fullname": f"Test User {i}",
            }
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse("update-user", kwargs={"pk": self.user.pk})
        for i in range(15):
            data = {"fullname": f"Updated Name {i}"}
            response = self.client.put(url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse("list-user")
        for _ in range(25):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse("update-role", kwargs={"pk": self.user.pk})
        for i in range(15):
            data = {"role": "admin" if i % 2 == 0 else "user"}
            response = self.client.patch(url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
