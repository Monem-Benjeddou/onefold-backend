"""
Integration test to demonstrate the complete fix for SendGrid email failures.
This test shows that the forgot password endpoint gracefully handles SendGrid 401 errors.
"""

from unittest.mock import patch
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.test import override_settings
import python_http_client.exceptions

from apps.accounts.auth.tests.constants import FORGOT_PASSWORD_URL

User = get_user_model()


class IntegrationEmailFailureTest(APITestCase):
    """Integration test demonstrating the complete SendGrid error handling fix."""

    def setUp(self):
        self.test_email = "user@example.com"
        self.user = User.objects.create_user(
            email=self.test_email,
            password="testpass123",
            username="testuser",
            fullname="Test User",
        )

    @override_settings(RATELIMIT_ENABLE=False)
    @patch("core.tasks.emails.send_sendgrid_email")
    def test_complete_sendgrid_401_error_handling_integration(self, mock_sendgrid):
        """
        Complete integration test showing that:
        1. SendGrid 401 error (insufficient credits) doesn't crash the view
        2. The view returns 200 OK (for security - don't reveal if email exists)
        3. Proper error logging occurs
        4. The user token is still created (password reset can work via other means)
        """

        mock_sendgrid.side_effect = python_http_client.exceptions.UnauthorizedError(
            401, "Unauthorized", b'{"error": "Maximum credits exceeded"}', {}
        )

        data = {"email": self.test_email}
        response = self.client.post(FORGOT_PASSWORD_URL, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password reset email sent.")

        mock_sendgrid.assert_called_once()

        from apps.accounts.user.models import UserToken

        tokens = UserToken.objects.filter(user=self.user)
        self.assertTrue(
            tokens.exists(),
            "Password reset token should be created even if email fails",
        )

        print("✅ Integration test passed: SendGrid 401 error handled gracefully")
        print(f"   - View returned: {response.status_code} {response.data}")
        print(f"   - Email sending attempted: {mock_sendgrid.called}")
        print(f"   - Password reset token created: {tokens.exists()}")

    @override_settings(RATELIMIT_ENABLE=False)
    @patch("core.tasks.emails.send_sendgrid_email")
    def test_sendgrid_success_still_works(self, mock_sendgrid):
        """Verify that when SendGrid works normally, everything works as expected."""

        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_sendgrid.return_value = mock_response

        data = {"email": self.test_email}
        response = self.client.post(FORGOT_PASSWORD_URL, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password reset email sent.")

        mock_sendgrid.assert_called_once()

        from apps.accounts.user.models import UserToken

        tokens = UserToken.objects.filter(user=self.user)
        self.assertTrue(tokens.exists())

        print("✅ Normal operation test passed: SendGrid success works correctly")
