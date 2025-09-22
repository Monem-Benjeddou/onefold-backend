import os
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.accounts.user.models import User, UserToken
from apps.accounts.auth.serializers.forgot_password_serializer import (
    ForgotPasswordSerializer,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()


class ForgotPasswordLinkTests(APITestCase):
    """
    Test forgot password functionality with FORGOT_PASSWORD_LINK environment variable.

    All users now receive the same reset link from FORGOT_PASSWORD_LINK environment variable,
    regardless of their role. This replaces the previous role-based URL system.
    """

    def setUp(self):

        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="testpass123",
            role="user",
        )

        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

        self.client = APIClient()
        self.forgot_password_url = reverse("auth-forgot-password")

        self.configured_link = (
            "https://landing-page-front-config.awqafintech.com/auth/reset-password"
        )

    @patch.dict(
        os.environ,
        {
            "FORGOT_PASSWORD_LINK": "https://landing-page-front-config.awqafintech.com/auth/reset-password"
        },
    )
    @patch(
        "apps.accounts.auth.serializers.forgot_password_serializer.send_activation_email"
    )
    def test_regular_user_reset_link(self, mock_send_email):
        """Test that regular users receive the FORGOT_PASSWORD_LINK from environment."""

        response = self.client.post(
            self.forgot_password_url, {"email": self.regular_user.email}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args

        self.assertIn(self.configured_link, call_args[0][1])

    @patch.dict(
        os.environ,
        {
            "FORGOT_PASSWORD_LINK": "https://landing-page-front-config.awqafintech.com/auth/reset-password"
        },
    )
    @patch(
        "apps.accounts.auth.serializers.forgot_password_serializer.send_activation_email"
    )
    def test_admin_reset_link(self, mock_send_email):
        """Test that admin users receive the same FORGOT_PASSWORD_LINK from environment."""

        response = self.client.post(
            self.forgot_password_url, {"email": self.admin_user.email}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args

        self.assertIn(self.configured_link, call_args[0][1])

    @patch.dict(os.environ, {"FORGOT_PASSWORD_LINK": "https://example.com/reset"})
    def test_serializer_link_method(self):
        """Test that the serializer gets the link from environment variable."""
        serializer = ForgotPasswordSerializer()
        link = serializer.get_forgot_password_link()
        self.assertEqual(link, "https://example.com/reset")

    @patch.dict(os.environ, {}, clear=True)
    def test_serializer_fallback_link(self):
        """Test that the serializer falls back to localhost when FORGOT_PASSWORD_LINK is not set."""
        serializer = ForgotPasswordSerializer()
        link = serializer.get_forgot_password_link()
        self.assertEqual(link, "http://localhost:5173/auth/reset-password")

    @patch.dict(
        os.environ,
        {
            "FORGOT_PASSWORD_LINK": "https://landing-page-front-config.awqafintech.com/auth/reset-password"
        },
    )
    @patch(
        "apps.accounts.auth.serializers.forgot_password_serializer.send_activation_email"
    )
    def test_token_generation(self, mock_send_email):
        """Test that password reset tokens are generated correctly."""

        response = self.client.post(
            self.forgot_password_url, {"email": self.regular_user.email}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token = UserToken.objects.filter(user=self.regular_user).first()
        self.assertIsNotNone(token)
        self.assertEqual(token.user, self.regular_user)

    def test_invalid_email(self):
        """Test password reset with invalid email."""

        response = self.client.post(
            self.forgot_password_url, {"email": "nonexistent@example.com"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch.dict(
        os.environ,
        {
            "FORGOT_PASSWORD_LINK": "https://landing-page-front-config.awqafintech.com/auth/reset-password"
        },
    )
    @patch(
        "apps.accounts.auth.serializers.forgot_password_serializer.send_activation_email"
    )
    def test_consistent_link_across_user_types(self, mock_send_email):
        """Test that all user types receive the same reset link."""

        response = self.client.post(
            self.forgot_password_url, {"email": self.regular_user.email}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            self.forgot_password_url, {"email": self.admin_user.email}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(mock_send_email.call_count, 2)

        first_call_args = mock_send_email.call_args_list[0]
        second_call_args = mock_send_email.call_args_list[1]

        self.assertIn(self.configured_link, first_call_args[0][1])
        self.assertIn(self.configured_link, second_call_args[0][1])
