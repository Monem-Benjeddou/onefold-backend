from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import uuid

from apps.accounts.user.models import User
from apps.accounts.user.serializers import UserSerializer


@override_settings(RATE_LIMITER_ENABLED=False)
class ListUsersViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("list-user")

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

        self.user1 = User.objects.create_user(
            username="testuser1",
            email="user1@example.com",
            password="Password123",
            fullname="Test User 1",
            role="user",
        )

        self.user2 = User.objects.create_user(
            username="testuser2",
            email="user2@example.com",
            password="Password123",
            fullname="Test User 2",
            role="admin",
        )

        self.client.force_authenticate(user=self.admin_user)

    def test_list_users_authenticated_as_admin(self):
        """Test listing users when authenticated as admin"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("meta", response.data)
        self.assertIn("results", response.data)

        self.assertEqual(len(response.data["results"]), 3)

    def test_list_users_unauthenticated(self):
        """Test that unauthenticated requests are rejected"""
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_users_as_regular_user(self):
        """Test that regular users cannot access the list"""
        self.client.force_authenticate(user=self.user1)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_users_with_search(self):
        """Test searching users by username/email/fullname"""
        response = self.client.get(f"{self.url}?search=test")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_emails = [user["email"] for user in response.data["results"]]
        self.assertIn(self.user1.email, user_emails)
        self.assertIn(self.user2.email, user_emails)

    def test_list_users_with_role_filter(self):
        """Test filtering users by role"""
        response = self.client.get(f"{self.url}?role=user")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_emails = [user["email"] for user in response.data["results"]]
        self.assertIn(self.user1.email, user_emails)
        self.assertNotIn(self.user2.email, user_emails)
