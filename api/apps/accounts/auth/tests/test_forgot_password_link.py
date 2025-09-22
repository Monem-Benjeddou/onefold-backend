"""
Tests for forgot password functionality with FORGOT_PASSWORD_LINK configuration.
"""

import os
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from apps.accounts.auth.serializers.forgot_password_serializer import (
    ForgotPasswordSerializer,
)
from apps.accounts.user.models import UserToken

User = get_user_model()


class ForgotPasswordLinkTest(TestCase):
    """Test forgot password link generation with environment variable configuration."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com", username="testuser", password="testpass123"
        )
        self.serializer_data = {"email": "test@example.com"}

    def test_forgot_password_link_from_env(self):
        """Test that forgot password link uses FORGOT_PASSWORD_LINK from environment."""
        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        ):
            with patch.dict(
                os.environ,
                {
                    "FORGOT_PASSWORD_LINK": "https://landing-page-front-config.awqafintech.com/auth/reset-password"
                },
            ):
                mail.outbox = []

                serializer = ForgotPasswordSerializer(data=self.serializer_data)
                self.assertTrue(serializer.is_valid())
                serializer.save()

                self.assertEqual(len(mail.outbox), 1)
                sent_email = mail.outbox[0]

                self.assertIn(
                    "https://landing-page-front-config.awqafintech.com/auth/reset-password",
                    sent_email.body,
                )
                self.assertIn("token=", sent_email.body)

    def test_forgot_password_link_fallback(self):
        """Test that forgot password link falls back to localhost when env var not set."""
        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        ):
            with patch.dict(os.environ, {}, clear=True):
                mail.outbox = []

                serializer = ForgotPasswordSerializer(data=self.serializer_data)
                self.assertTrue(serializer.is_valid())
                serializer.save()

                self.assertEqual(len(mail.outbox), 1)
                sent_email = mail.outbox[0]

                self.assertIn(
                    "http://localhost:5173/auth/reset-password", sent_email.body
                )
                self.assertIn("token=", sent_email.body)

    def test_get_forgot_password_link_method(self):
        """Test the get_forgot_password_link method directly."""
        serializer = ForgotPasswordSerializer()

        with patch.dict(
            os.environ, {"FORGOT_PASSWORD_LINK": "https://example.com/reset"}
        ):
            link = serializer.get_forgot_password_link()
            self.assertEqual(link, "https://example.com/reset")

        with patch.dict(os.environ, {}, clear=True):
            link = serializer.get_forgot_password_link()
            self.assertEqual(link, "http://localhost:5173/auth/reset-password")

    def test_token_generation_and_storage(self):
        """Test that token is properly generated and stored."""
        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        ):
            with patch.dict(
                os.environ, {"FORGOT_PASSWORD_LINK": "https://example.com/reset"}
            ):
                mail.outbox = []

                UserToken.objects.filter(user=self.user).delete()

                serializer = ForgotPasswordSerializer(data=self.serializer_data)
                self.assertTrue(serializer.is_valid())
                serializer.save()

                user_token = UserToken.objects.get(user=self.user)
                self.assertIsNotNone(user_token.token)

                token_generator = PasswordResetTokenGenerator()
                self.assertTrue(
                    token_generator.check_token(self.user, user_token.token)
                )

    def test_invalid_email_validation(self):
        """Test that invalid email addresses are properly rejected."""
        invalid_data = {"email": "nonexistent@example.com"}

        serializer = ForgotPasswordSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertIn("User does not exist", str(serializer.errors["email"]))


class ForgotPasswordAPITest(APITestCase):
    """Test forgot password API endpoint with new link configuration."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="api-test@example.com", username="apiuser", password="testpass123"
        )
        self.forgot_password_url = reverse("auth-forgot-password")
        self.valid_data = {"email": "api-test@example.com"}

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_forgot_password_api_with_env_link(self):
        """Test forgot password API endpoint with FORGOT_PASSWORD_LINK from environment."""
        with patch.dict(
            os.environ,
            {
                "FORGOT_PASSWORD_LINK": "https://landing-page-front-config.awqafintech.com/auth/reset-password"
            },
        ):
            mail.outbox = []

            response = self.client.post(
                self.forgot_password_url, self.valid_data, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("message", response.data)
            self.assertEqual(response.data["message"], "Password reset email sent.")

            self.assertEqual(len(mail.outbox), 1)
            sent_email = mail.outbox[0]
            self.assertEqual(sent_email.to, ["api-test@example.com"])
            self.assertIn(
                "https://landing-page-front-config.awqafintech.com/auth/reset-password",
                sent_email.body,
            )

    def test_forgot_password_api_invalid_email(self):
        """Test forgot password API with invalid email."""
        invalid_data = {"email": "invalid@example.com"}

        response = self.client.post(
            self.forgot_password_url, invalid_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("email", response.data["error"])

    def test_forgot_password_api_missing_email(self):
        """Test forgot password API with missing email field."""
        invalid_data = {}

        response = self.client.post(
            self.forgot_password_url, invalid_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("email", response.data["error"])

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_forgot_password_link_token_format(self):
        """Test that the generated link has the correct token format."""
        with patch.dict(os.environ, {"FORGOT_PASSWORD_LINK": "https://test.com/reset"}):
            mail.outbox = []

            response = self.client.post(
                self.forgot_password_url, self.valid_data, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            sent_email = mail.outbox[0]
            email_body = sent_email.body

            self.assertIn("https://test.com/reset?token=", email_body)

            token_start = email_body.find("token=") + 6
            token_end = email_body.find("\n", token_start)
            if token_end == -1:
                token_end = len(email_body)
            token = email_body[token_start:token_end].strip()

            self.assertGreater(len(token), 10)
            self.assertNotIn(" ", token)
