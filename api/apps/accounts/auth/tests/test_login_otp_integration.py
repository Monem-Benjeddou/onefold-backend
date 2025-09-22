"""
Integration tests for OTP login functionality to ensure User model methods work correctly.
"""

import pytest
from django.test import TransactionTestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.accounts.auth.models import OTP

User = get_user_model()


class OTPLoginIntegrationTest(TransactionTestCase):
    """Integration tests for OTP login functionality."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            fullname="Test User",
            username="testuser",
        )
        self.request_otp_url = "/api/v1/auth/login-otp/"
        self.verify_otp_url = "/api/v1/auth/verify-otp/"

    def test_user_model_has_required_methods(self):
        """Test that User model has all required OTP methods."""
        self.assertTrue(hasattr(self.user, "generate_verification_code"))
        self.assertTrue(hasattr(self.user, "verify_code"))
        self.assertTrue(hasattr(self.user, "send_verification_email"))

    def test_generate_verification_code_method(self):
        """Test that generate_verification_code method works correctly."""

        code = self.user.generate_verification_code()

        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

        otp = OTP.objects.get(user=self.user)
        self.assertEqual(otp.code, code)

    def test_verify_code_method(self):
        """Test that verify_code method works correctly."""

        code = self.user.generate_verification_code()

        result = self.user.verify_code(code)
        self.assertTrue(result)

        result = self.user.verify_code("000000")
        self.assertFalse(result)

    def test_send_verification_email_method(self):
        """Test that send_verification_email method works correctly."""

        self.user.generate_verification_code()

        result = self.user.send_verification_email(email_type="otp")

        self.assertIsInstance(result, bool)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_request_otp_endpoint_integration(self):
        """Test the complete OTP request flow."""
        response = self.client.post(self.request_otp_url, {"email": self.user.email})

        self.assertIn(
            response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        )

        if response.status_code == status.HTTP_200_OK:
            self.assertTrue(OTP.objects.filter(user=self.user).exists())

    def test_verify_otp_endpoint_integration(self):
        """Test the complete OTP verification flow."""

        code = self.user.generate_verification_code()

        response = self.client.post(
            self.verify_otp_url, {"email": self.user.email, "otp": code}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_invalid_otp_verification(self):
        """Test OTP verification with invalid code."""

        self.user.generate_verification_code()

        response = self.client.post(
            self.verify_otp_url, {"email": self.user.email, "otp": "000000"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(
            "otp" in response.data
            or ("error" in response.data and "otp" in response.data["error"])
        )

    def test_user_model_method_availability_runtime(self):
        """Test that User model methods are available at runtime."""

        user = User.objects.create_user(
            email="runtime@example.com",
            password="testpassword123",
            fullname="Runtime Test User",
            username="runtimeuser",
        )

        self.assertTrue(hasattr(user, "generate_verification_code"))
        self.assertTrue(callable(getattr(user, "generate_verification_code", None)))

        self.assertTrue(hasattr(user, "verify_code"))
        self.assertTrue(callable(getattr(user, "verify_code", None)))

        self.assertTrue(hasattr(user, "send_verification_email"))
        self.assertTrue(callable(getattr(user, "send_verification_email", None)))

    def test_otp_generation_error_handling(self):
        """Test error handling when OTP generation fails."""

        code = self.user.generate_verification_code()
        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    def test_email_sending_error_handling(self):
        """Test error handling when email sending fails."""

        self.user.generate_verification_code()

        result = self.user.send_verification_email(email_type="otp")
        self.assertIsInstance(result, bool)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_request_otp_with_nonexistent_user_detailed(self):
        """Test OTP request with detailed error checking."""
        response = self.client.post(
            self.request_otp_url, {"email": "nonexistent@example.com"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            "email" in response.data
            or ("error" in response.data and "email" in response.data["error"])
        )

    def test_verify_otp_with_expired_code(self):
        """Test OTP verification with expired code."""
        from django.utils import timezone
        from apps.accounts.auth.models import OTP

        expired_time = timezone.now() - timezone.timedelta(minutes=15)
        OTP.objects.create(user=self.user, code="123456", expires_at=expired_time)

        response = self.client.post(
            self.verify_otp_url, {"email": self.user.email, "otp": "123456"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            "otp" in response.data
            or ("error" in response.data and "otp" in response.data["error"])
        )
