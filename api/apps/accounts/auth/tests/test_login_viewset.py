from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class LoginViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = "/api/v1/auth/login/"

        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            fullname="Test User",
            username="testuser",
        )

    def test_login_viewset_case_insensitive_email(self):
        """Test that the login viewset handles case-insensitive emails."""

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

    def test_login_viewset_invalid_credentials(self):
        """Test that the login viewset rejects invalid credentials."""
        data = {"email": "user@example.com", "password": "wrongpassword"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_viewset_nonexistent_user(self):
        """Test that the login viewset rejects non-existent users."""
        data = {"email": "nonexistent@example.com", "password": "password123"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
