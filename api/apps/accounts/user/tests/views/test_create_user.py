from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.user.models import User


@override_settings(RATE_LIMITER_ENABLED=False)
class CreateUserViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("create-user")

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="Password123",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

        self.client.force_authenticate(user=self.admin_user)

        self.valid_data = {
            "email": "newuser@example.com",
            "fullname": "New Test User",
            "role": "user",
        }

    def test_create_user_authenticated_as_admin(self):
        """Test creating a user when authenticated as admin"""
        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], self.valid_data["email"])
        self.assertEqual(response.data["fullname"], self.valid_data["fullname"])
        self.assertEqual(response.data["role"], self.valid_data["role"])

        self.assertTrue(User.objects.filter(email=self.valid_data["email"]).exists())

    def test_create_user_no_role_provided(self):
        """Test creating a user without specifying a role (should use default)"""
        data = self.valid_data.copy()
        data.pop("role")

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_user = User.objects.get(email=data["email"])
        self.assertEqual(created_user.role, "user")

    def test_create_user_missing_email(self):
        """Test creating a user without an email address"""
        data = self.valid_data.copy()
        data.pop("email")

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_missing_fullname(self):
        """Test creating a user without a fullname"""
        data = self.valid_data.copy()
        data.pop("fullname")

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_unauthenticated(self):
        """Test that unauthenticated requests are rejected"""
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_as_regular_user(self):
        """Test that regular users cannot create users"""
        regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="Password123",
            role="user",
        )
        self.client.force_authenticate(user=regular_user)

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
