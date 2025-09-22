"""
Test forgot password functionality with email sending failures.
Tests that the forgot password view gracefully handles SendGrid errors.
"""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.core import mail
import python_http_client.exceptions

from apps.accounts.auth.tests.constants import FORGOT_PASSWORD_URL
from core.tasks.emails import send_activation_email, send_sendgrid_email

User = get_user_model()


class ForgotPasswordEmailFailureTests(APITestCase):
    """Test that forgot password works gracefully when email sending fails."""

    def setUp(self):
        self.client = APIClient()
        self.test_email = "test@example.com"
        self.user = User.objects.create_user(
            email=self.test_email,
            password="testpass123",
            username="testuser",
            fullname="Test User",
        )

    @override_settings(RATELIMIT_ENABLE=False)
    @patch("core.tasks.emails.send_sendgrid_email")
    def test_forgot_password_sendgrid_unauthorized_error_graceful(self, mock_sendgrid):
        """Test that UnauthorizedError from SendGrid doesn't crash the view."""

        mock_sendgrid.side_effect = python_http_client.exceptions.UnauthorizedError(
            401, "Unauthorized", b'{"error": "Maximum credits exceeded"}', {}
        )

        data = {"email": self.test_email}
        response = self.client.post(FORGOT_PASSWORD_URL, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password reset email sent.")

        mock_sendgrid.assert_called_once()

    @override_settings(RATELIMIT_ENABLE=False)
    @patch("core.tasks.emails.send_sendgrid_email")
    def test_forgot_password_sendgrid_forbidden_error_graceful(self, mock_sendgrid):
        """Test that ForbiddenError from SendGrid doesn't crash the view."""
        mock_sendgrid.side_effect = python_http_client.exceptions.ForbiddenError(
            403, "Forbidden", b'{"error": "Forbidden"}', {}
        )

        data = {"email": self.test_email}
        response = self.client.post(FORGOT_PASSWORD_URL, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password reset email sent.")

    @override_settings(RATELIMIT_ENABLE=False)
    @patch("core.tasks.emails.send_sendgrid_email")
    def test_forgot_password_sendgrid_bad_request_error_graceful(self, mock_sendgrid):
        """Test that BadRequestsError from SendGrid doesn't crash the view."""
        mock_sendgrid.side_effect = python_http_client.exceptions.BadRequestsError(
            400, "Bad Request", b'{"error": "Bad Request"}', {}
        )

        data = {"email": self.test_email}
        response = self.client.post(FORGOT_PASSWORD_URL, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password reset email sent.")

    @override_settings(RATELIMIT_ENABLE=False)
    @patch("core.tasks.emails.send_sendgrid_email")
    def test_forgot_password_generic_email_error_graceful(self, mock_sendgrid):
        """Test that generic email errors don't crash the view."""
        mock_sendgrid.side_effect = Exception("Network timeout or other error")

        data = {"email": self.test_email}
        response = self.client.post(FORGOT_PASSWORD_URL, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password reset email sent.")

    @override_settings(RATELIMIT_ENABLE=False)
    @patch("core.tasks.emails.send_sendgrid_email")
    def test_forgot_password_email_success_still_works(self, mock_sendgrid):
        """Test that successful email sending still works properly."""

        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_sendgrid.return_value = mock_response

        data = {"email": self.test_email}
        response = self.client.post(FORGOT_PASSWORD_URL, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password reset email sent.")

        mock_sendgrid.assert_called_once()

    @override_settings(RATELIMIT_ENABLE=False)
    def test_forgot_password_invalid_email_still_fails_properly(self):
        """Test that invalid emails still return proper validation errors."""
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(FORGOT_PASSWORD_URL, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User does not exist", str(response.data))

    def test_send_activation_email_returns_false_on_unauthorized_error(self):
        """Test that send_activation_email returns False on UnauthorizedError."""
        with patch("core.tasks.emails.send_sendgrid_email") as mock_sendgrid:
            mock_sendgrid.side_effect = python_http_client.exceptions.UnauthorizedError(
                401, "Unauthorized", b'{"error": "Maximum credits exceeded"}', {}
            )

            result = send_activation_email(
                subject="Test Subject",
                text_content="Test content",
                to_email=self.test_email,
                html_content="<p>Test HTML</p>",
            )

            self.assertFalse(result)
            mock_sendgrid.assert_called_once()

    def test_send_activation_email_returns_false_on_generic_error(self):
        """Test that send_activation_email returns False on generic errors."""
        with patch("core.tasks.emails.send_sendgrid_email") as mock_sendgrid:
            mock_sendgrid.side_effect = Exception("Network error")

            result = send_activation_email(
                subject="Test Subject",
                text_content="Test content",
                to_email=self.test_email,
            )

            self.assertFalse(result)

    def test_send_activation_email_returns_true_on_success(self):
        """Test that send_activation_email returns True on success."""
        with patch("core.tasks.emails.send_sendgrid_email") as mock_sendgrid:
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_sendgrid.return_value = mock_response

            result = send_activation_email(
                subject="Test Subject",
                text_content="Test content",
                to_email=self.test_email,
            )

            self.assertTrue(result)

    @override_settings(RATELIMIT_ENABLE=False)
    @patch("apps.accounts.auth.serializers.forgot_password_serializer.logger")
    @patch("core.tasks.emails.send_sendgrid_email")
    def test_forgot_password_logs_email_failure(self, mock_sendgrid, mock_logger):
        """Test that email failures are properly logged."""
        mock_sendgrid.side_effect = python_http_client.exceptions.UnauthorizedError(
            401, "Unauthorized", b'{"error": "Maximum credits exceeded"}', {}
        )

        data = {"email": self.test_email}
        response = self.client.post(FORGOT_PASSWORD_URL, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args[0][0]
        self.assertIn("Password reset email failed to send", warning_call)
        self.assertIn(self.test_email, warning_call)

    @override_settings(RATELIMIT_ENABLE=False)
    @patch("core.tasks.emails.logger")
    @patch("core.tasks.emails.send_sendgrid_email")
    def test_email_task_logs_unauthorized_error(self, mock_sendgrid, mock_logger):
        """Test that the email task logs UnauthorizedError appropriately."""
        mock_sendgrid.side_effect = python_http_client.exceptions.UnauthorizedError(
            401, "Unauthorized", b'{"error": "Maximum credits exceeded"}', {}
        )

        result = send_activation_email(
            subject="Test Subject",
            text_content="Test content",
            to_email=self.test_email,
        )

        self.assertFalse(result)

        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        self.assertIn("SendGrid unauthorized error", error_call)
        self.assertIn(self.test_email, error_call)
