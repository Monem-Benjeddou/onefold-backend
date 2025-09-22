"""
Comprehensive tests to ensure OTP is exactly 6 numeric digits.
Tests OTP generation, validation, and serializer constraints.
"""

import re
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from apps.accounts.auth.models import OTP
from apps.accounts.auth.utils import generate_otp
from apps.accounts.auth.serializers.login_otp import OTPVerifySerializer


User = get_user_model()


class OTPSixDigitsTest(TransactionTestCase):
    """Test that OTP is exactly 6 numeric digits."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            fullname="Test User",
            username="testuser",
        )

    def test_generate_otp_function_returns_6_digits(self):
        """Test that generate_otp() returns exactly 6 numeric digits."""
        for _ in range(100):
            otp = generate_otp()

            self.assertEqual(len(otp), 6, f"OTP '{otp}' is not 6 characters long")

            self.assertTrue(otp.isdigit(), f"OTP '{otp}' contains non-digit characters")

            self.assertRegex(
                otp, r"^\d{6}$", f"OTP '{otp}' doesn't match 6-digit pattern"
            )

    def test_generate_otp_no_letters_or_special_chars(self):
        """Test that generate_otp() never contains letters or special characters."""
        for _ in range(50):
            otp = generate_otp()

            self.assertFalse(
                re.search(r"[a-zA-Z]", otp), f"OTP '{otp}' contains letters"
            )

            self.assertFalse(
                re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\?]', otp),
                f"OTP '{otp}' contains special characters",
            )

    def test_user_generate_verification_code_creates_6_digit_otp(self):
        """Test that User.generate_verification_code() creates 6-digit OTP."""
        code = self.user.generate_verification_code()

        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

        otp = OTP.objects.get(user=self.user)
        self.assertEqual(len(otp.code), 6)
        self.assertTrue(otp.code.isdigit())
        self.assertEqual(otp.code, code)

    def test_otp_model_field_constraints(self):
        """Test that OTP model enforces 6-character limit."""

        otp_6 = OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        self.assertEqual(len(otp_6.code), 6)

        field = OTP._meta.get_field("code")
        self.assertEqual(field.max_length, 6)

    def test_otp_verify_serializer_validation(self):
        """Test that OTPVerifySerializer validates 6-digit numeric input."""

        serializer = OTPVerifySerializer(
            data={"email": "test@example.com", "otp": "123456"}
        )
        self.assertTrue(serializer.is_valid())

        serializer = OTPVerifySerializer(
            data={"email": "test@example.com", "otp": "12345"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("otp", serializer.errors)

        serializer = OTPVerifySerializer(
            data={"email": "test@example.com", "otp": "1234567"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("otp", serializer.errors)

        serializer = OTPVerifySerializer(
            data={"email": "test@example.com", "otp": "12345a"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("otp", serializer.errors)

        serializer = OTPVerifySerializer(
            data={"email": "test@example.com", "otp": "12345!"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("otp", serializer.errors)

    def test_verify_otp_serializer_validation(self):
        """Test that OTPVerifySerializer validates 6-digit numeric input."""

        OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )

        serializer = OTPVerifySerializer(
            data={"email": self.user.email, "otp": "123456"}
        )
        self.assertTrue(
            serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        )

        serializer = OTPVerifySerializer(
            data={"email": self.user.email, "otp": "12345"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("otp", serializer.errors)

        serializer = OTPVerifySerializer(
            data={"email": self.user.email, "otp": "12345678"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("otp", serializer.errors)

        serializer = OTPVerifySerializer(
            data={"email": self.user.email, "otp": "abc123"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("otp", serializer.errors)

    def test_otp_uniqueness_across_generations(self):
        """Test that multiple OTP generations produce different codes."""
        codes = set()
        for _ in range(20):
            code = generate_otp()
            codes.add(code)

        self.assertGreater(
            len(codes), 15, "OTP generation seems to be producing too many duplicates"
        )

    def test_otp_range_coverage(self):
        """Test that OTP generation covers the full range of possible digits."""
        all_digits = set()
        for _ in range(200):
            otp = generate_otp()
            all_digits.update(otp)

        self.assertGreaterEqual(
            len(all_digits), 8, "OTP generation doesn't seem to use full digit range"
        )

        for digit in all_digits:
            self.assertIn(digit, "0123456789", f"Found non-digit character: {digit}")


class OTPAPIEndpointTest(TransactionTestCase):
    """Test OTP API endpoints with 6-digit validation."""

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

    @patch("apps.accounts.user.models.User.send_verification_email")
    def test_request_otp_generates_6_digit_code(self, mock_send_email):
        """Test that requesting OTP generates exactly 6 digits."""
        mock_send_email.return_value = True

        with self.settings(RATELIMIT_ENABLE=False, OTP_DELIVERY_METHOD="email"):
            response = self.client.post(
                self.request_otp_url, {"email": self.user.email}
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        otp = OTP.objects.get(user=self.user)
        self.assertEqual(len(otp.code), 6)
        self.assertTrue(otp.code.isdigit())

    def test_verify_otp_rejects_invalid_formats(self):
        """Test that OTP verification rejects non-6-digit formats."""

        self.user.generate_verification_code()

        invalid_otps = [
            "12345",
            "1234567",
            "12345678",
            "abcdef",
            "12345a",
            "123!@#",
            "",
            "   123456",
        ]

        for invalid_otp in invalid_otps:
            response = self.client.post(
                self.verify_otp_url, {"email": self.user.email, "otp": invalid_otp}
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"Should reject invalid OTP: '{invalid_otp}'",
            )

    def test_verify_otp_accepts_valid_6_digit_code(self):
        """Test that OTP verification accepts valid 6-digit codes."""

        code = self.user.generate_verification_code()

        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

        response = self.client.post(
            self.verify_otp_url, {"email": self.user.email, "otp": code}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
