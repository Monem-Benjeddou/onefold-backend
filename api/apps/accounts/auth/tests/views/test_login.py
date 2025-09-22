from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date

User = get_user_model()


class LoginViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = "/api/v1/auth/login/"

        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            fullname="Test User",
            username="testuser",
        )

    def test_login_view_case_insensitive_email(self):
        """Test that the login view handles case-insensitive emails."""

        data = {"email": "USER@EXAMPLE.COM", "password": "password123"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)

        data = {"email": "UsEr@eXaMpLe.CoM", "password": "password123"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

        data = {"email": "user@example.com", "password": "password123"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_view_invalid_credentials(self):
        """Test that the login view rejects invalid credentials."""
        data = {"email": "user@example.com", "password": "wrongpassword"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_view_nonexistent_user(self):
        """Test that the login view rejects non-existent users."""
        data = {"email": "nonexistent@example.com", "password": "password123"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_response_includes_date_of_birth(self):
        """Test that the login response includes date_of_birth field."""

        test_date = date(1990, 5, 15)
        user_with_dob = User.objects.create_user(
            email="user_with_dob@example.com",
            password="password123",
            fullname="User With DOB",
            username="userdob",
            date_of_birth=test_date,
        )

        data = {"email": "user_with_dob@example.com", "password": "password123"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIn("date_of_birth", response.data["user"])
        self.assertEqual(response.data["user"]["date_of_birth"], "1990-05-15")

    def test_login_response_includes_date_of_birth_null(self):
        """Test that the login response includes date_of_birth field even when null."""
        data = {"email": "user@example.com", "password": "password123"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIn("date_of_birth", response.data["user"])
        self.assertIsNone(response.data["user"]["date_of_birth"])

    def test_login_unverified_user_fails(self):
        """Test that login fails for unverified users."""

        unverified_user = User.objects.create_user(
            email="unverified@example.com",
            password="password123",
            fullname="Unverified User",
            username="unverified",
            is_active=False,
        )

        data = {"email": "unverified@example.com", "password": "password123"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertIn("not verified", response.data["error"].lower())
