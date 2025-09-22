"""
Tests for password reset email with token display functionality.
"""

import os
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.template.loader import render_to_string
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import re

from apps.accounts.auth.serializers.forgot_password_serializer import (
    ForgotPasswordSerializer,
)
from apps.accounts.user.models import UserToken

User = get_user_model()


class PasswordResetTokenEmailTest(TestCase):
    """Test password reset email includes token display."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com", username="testuser", password="testpass123"
        )
        self.serializer_data = {"email": "test@example.com"}

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_contains_token_in_body(self):
        """Test that the email body contains the token."""
        with patch.dict(
            os.environ, {"FORGOT_PASSWORD_LINK": "https://example.com/reset"}
        ):
            mail.outbox = []

            serializer = ForgotPasswordSerializer(data=self.serializer_data)
            self.assertTrue(serializer.is_valid())
            serializer.save()

            self.assertEqual(len(mail.outbox), 1)
            sent_email = mail.outbox[0]

            self.assertIn("Reset Token:", sent_email.body)

            token_match = re.search(r"Reset Token: (\S+)", sent_email.body)
            self.assertIsNotNone(token_match)
            token = token_match.group(1)

            token_generator = PasswordResetTokenGenerator()
            self.assertTrue(token_generator.check_token(self.user, token))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_html_contains_token(self):
        """Test that the HTML email contains the token."""
        with patch.dict(
            os.environ, {"FORGOT_PASSWORD_LINK": "https://example.com/reset"}
        ):
            mail.outbox = []

            serializer = ForgotPasswordSerializer(data=self.serializer_data)
            self.assertTrue(serializer.is_valid())
            serializer.save()

            self.assertEqual(len(mail.outbox), 1)
            sent_email = mail.outbox[0]

            html_content = None
            for content, content_type in sent_email.alternatives:
                if content_type == "text/html":
                    html_content = content
                    break

            self.assertIsNotNone(html_content)
            self.assertIn("Reset Token:", html_content)
            self.assertIn("code-block", html_content)

    def test_token_in_template_context(self):
        """Test that token is passed to the email template."""
        token = "test-token-123456"
        reset_url = "https://example.com/reset?token=test-token-123456"

        html_content = render_to_string(
            "forgot_password_email.html", {"reset_url": reset_url, "token": token}
        )

        self.assertIn("Reset Token:", html_content)
        self.assertIn(token, html_content)
        self.assertIn(reset_url, html_content)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_token_matches_in_url_and_display(self):
        """Test that the token in URL matches the displayed token."""
        with patch.dict(
            os.environ, {"FORGOT_PASSWORD_LINK": "https://example.com/reset"}
        ):
            mail.outbox = []

            serializer = ForgotPasswordSerializer(data=self.serializer_data)
            self.assertTrue(serializer.is_valid())
            serializer.save()

            sent_email = mail.outbox[0]
            email_body = sent_email.body

            url_match = re.search(r"token=(\S+?)(?:\s|$)", email_body)
            self.assertIsNotNone(url_match)
            url_token = url_match.group(1)

            display_match = re.search(r"Reset Token: (\S+)", email_body)
            self.assertIsNotNone(display_match)
            display_token = display_match.group(1)

            self.assertEqual(url_token, display_token)


class PasswordResetTokenAPITest(APITestCase):
    """Test password reset API with token display functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="api-test@example.com", username="apiuser", password="testpass123"
        )
        self.forgot_password_url = reverse("auth-forgot-password")
        self.valid_data = {"email": "api-test@example.com"}

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_api_sends_email_with_token(self):
        """Test that API endpoint sends email with token displayed."""
        with patch.dict(os.environ, {"FORGOT_PASSWORD_LINK": "https://test.com/reset"}):
            mail.outbox = []

            response = self.client.post(
                self.forgot_password_url, self.valid_data, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(mail.outbox), 1)

            sent_email = mail.outbox[0]

            self.assertIn("Reset Token:", sent_email.body)

            html_content = None
            for content, content_type in sent_email.alternatives:
                if content_type == "text/html":
                    html_content = content
                    break

            self.assertIsNotNone(html_content)
            self.assertIn("Reset Token:", html_content)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_multiple_requests_send_emails_with_tokens(self):
        """Test that multiple password reset requests send emails with tokens."""
        with patch.dict(os.environ, {"FORGOT_PASSWORD_LINK": "https://test.com/reset"}):
            mail.outbox = []

            response1 = self.client.post(
                self.forgot_password_url, self.valid_data, format="json"
            )
            self.assertEqual(response1.status_code, status.HTTP_200_OK)

            response2 = self.client.post(
                self.forgot_password_url, self.valid_data, format="json"
            )
            self.assertEqual(response2.status_code, status.HTTP_200_OK)

            self.assertEqual(len(mail.outbox), 2)

            token1_match = re.search(r"Reset Token: (\S+)", mail.outbox[0].body)
            token2_match = re.search(r"Reset Token: (\S+)", mail.outbox[1].body)

            self.assertIsNotNone(token1_match)
            self.assertIsNotNone(token2_match)

            token1 = token1_match.group(1)
            token2 = token2_match.group(1)

            self.assertGreaterEqual(len(token1), 20)
            self.assertGreaterEqual(len(token2), 20)

            token_generator = PasswordResetTokenGenerator()
            self.assertTrue(token_generator.check_token(self.user, token1))
            self.assertTrue(token_generator.check_token(self.user, token2))

    def test_token_format_and_security(self):
        """Test that generated tokens have appropriate format and security."""
        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        ):
            with patch.dict(
                os.environ, {"FORGOT_PASSWORD_LINK": "https://test.com/reset"}
            ):
                mail.outbox = []

                serializer = ForgotPasswordSerializer(data=self.valid_data)
                self.assertTrue(serializer.is_valid())
                serializer.save()

                sent_email = mail.outbox[0]
                token_match = re.search(r"Reset Token: (\S+)", sent_email.body)
                token = token_match.group(1)

                self.assertGreaterEqual(len(token), 20)

                self.assertNotIn(" ", token)
                self.assertNotIn("\n", token)
                self.assertNotIn("\r", token)

                self.assertRegex(token, r"^[A-Za-z0-9\-_]+$")


class PasswordResetTokenEdgeCasesTest(TestCase):
    """Test edge cases for password reset token email functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="edge-test@example.com", username="edgeuser", password="testpass123"
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_notification_with_valid_format(self):
        """Test that email notifications contain the token with proper format."""

        test_user = User.objects.create_user(
            email="valid-test@example.com", username="validuser", password="testpass123"
        )

        with patch.dict(os.environ, {"FORGOT_PASSWORD_LINK": "https://test.com/reset"}):
            mail.outbox = []

            serializer_data = {"email": "valid-test@example.com"}
            serializer = ForgotPasswordSerializer(data=serializer_data)
            self.assertTrue(serializer.is_valid())
            serializer.save()

            self.assertEqual(len(mail.outbox), 1)
            email_content = mail.outbox[0].body

            self.assertIn("Reset Token:", email_content)

            token_match = re.search(r"Reset Token: (\S+)", email_content)
            self.assertIsNotNone(token_match)
            token = token_match.group(1)
            self.assertGreaterEqual(len(token), 20)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_token_storage_and_retrieval(self):
        """Test that token is properly stored and can be retrieved."""
        with patch.dict(os.environ, {"FORGOT_PASSWORD_LINK": "https://test.com/reset"}):
            mail.outbox = []

            UserToken.objects.filter(user=self.user).delete()

            serializer_data = {"email": "edge-test@example.com"}
            serializer = ForgotPasswordSerializer(data=serializer_data)
            self.assertTrue(serializer.is_valid())
            serializer.save()

            sent_email = mail.outbox[0]
            token_match = re.search(r"Reset Token: (\S+)", sent_email.body)
            email_token = token_match.group(1)

            stored_token = UserToken.objects.get(user=self.user)
            self.assertEqual(stored_token.token, email_token)

    def test_email_template_rendering_with_special_characters(self):
        """Test email template renders correctly with special characters in token."""

        token = "test-token_with-special_chars-123"
        reset_url = f"https://example.com/reset?token={token}"

        html_content = render_to_string(
            "forgot_password_email.html", {"reset_url": reset_url, "token": token}
        )

        self.assertIn(token, html_content)
        self.assertIn('class="code-block"', html_content)
