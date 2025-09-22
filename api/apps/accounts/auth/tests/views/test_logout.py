from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

User = get_user_model()


class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.logout_url = "/api/v1/auth/logout/"

        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            fullname="Test User",
            username="testuser",
        )

        self.refresh_token = RefreshToken.for_user(self.user)
        self.access_token = self.refresh_token.access_token

    def test_logout_view_success(self):
        """Test successful logout"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"refresh": str(self.refresh_token)}
        response = self.client.post(self.logout_url, data)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        outstanding_token = OutstandingToken.objects.filter(
            token=str(self.refresh_token)
        ).first()
        self.assertIsNotNone(outstanding_token)

        blacklisted_token = BlacklistedToken.objects.filter(
            token=outstanding_token
        ).first()
        self.assertIsNotNone(blacklisted_token)

    def test_logout_view_without_refresh_token(self):
        """Test that logout fails without a refresh token"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        response = self.client.post(self.logout_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = response.json()

        self.assertIn("error", response_data)
        self.assertIn("refresh", response_data["error"])

    def test_logout_view_with_empty_refresh_token(self):
        """Test that logout fails with empty refresh token"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"refresh": ""}
        response = self.client.post(self.logout_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_view_with_null_refresh_token(self):
        """Test that logout fails with null refresh token"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"refresh": None}
        response = self.client.post(self.logout_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_view_with_invalid_refresh_token(self):
        """Test that logout fails with invalid refresh token"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"refresh": "invalid_token_here"}
        response = self.client.post(self.logout_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.json())

    def test_logout_view_with_malformed_refresh_token(self):
        """Test that logout fails with malformed refresh token"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"refresh": "malformed.token.here"}
        response = self.client.post(self.logout_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_view_with_expired_refresh_token(self):
        """Test that logout fails with expired refresh token"""

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MzM3MjI2MzJ9.invalid"
        }
        response = self.client.post(self.logout_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_view_double_logout(self):
        """Test that double logout (already blacklisted token) fails gracefully"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"refresh": str(self.refresh_token)}

        response1 = self.client.post(self.logout_url, data)
        self.assertEqual(response1.status_code, status.HTTP_204_NO_CONTENT)

        response2 = self.client.post(self.logout_url, data)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_view_unauthenticated(self):
        """Test that unauthenticated users cannot logout"""
        data = {"refresh": str(self.refresh_token)}
        response = self.client.post(self.logout_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_view_with_different_user_token(self):
        """Test that user cannot logout with another user's token"""

        other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
            fullname="Other User",
            username="otheruser",
        )
        other_refresh_token = RefreshToken.for_user(other_user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"refresh": str(other_refresh_token)}
        response = self.client.post(self.logout_url, data)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_view_response_headers(self):
        """Test that logout response has correct headers"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        data = {"refresh": str(self.refresh_token)}
        response = self.client.post(self.logout_url, data)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.content), 0)

    def test_logout_view_serializer_validation(self):
        """Test that logout properly validates using serializer"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        response = self.client.post(self.logout_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = response.json()

        self.assertTrue(
            "refresh" in response_data
            or ("error" in response_data and "refresh" in response_data["error"])
        )

    def test_logout_view_content_type(self):
        """Test that logout works with different content types"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        fresh_refresh_token = RefreshToken.for_user(self.user)

        data = {"refresh": str(fresh_refresh_token)}
        response = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
