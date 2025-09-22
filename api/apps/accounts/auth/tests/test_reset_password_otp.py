from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from apps.accounts.auth.models import OTP

User = get_user_model()


class ResetPasswordOTPTests(TestCase):
    """
    Test suite for reset password OTP functionality.
    """

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.reset_password_otp_url = reverse("auth-reset-password-otp")

        self.user = User.objects.create_user(
            email="test@example.com",
            password="oldpassword123",
            fullname="Test User",
            username="testuser",
        )

        self.otp_code = self.user.generate_verification_code()

    def tearDown(self):
        """Clean up after tests."""
        User.objects.all().delete()
        OTP.objects.all().delete()

    @override_settings(RATELIMIT_ENABLE=False)
    def test_reset_password_otp_invalid_otp(self):
        """Test password reset with invalid OTP."""
        response = self.client.post(
            self.reset_password_otp_url,
            {
                "email": self.user.email,
                "otp": "123456",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)
        self.assertEqual(response.data["otp"][0], "Invalid or expired OTP.")

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("oldpassword123"))

    @override_settings(RATELIMIT_ENABLE=False)
    def test_reset_password_otp_expired_otp(self):
        """Test password reset with expired OTP."""

        expired_time = timezone.now() - timezone.timedelta(minutes=15)
        OTP.objects.filter(user=self.user).delete()
        OTP.objects.create(user=self.user, code="123456", expires_at=expired_time)

        response = self.client.post(
            self.reset_password_otp_url,
            {
                "email": self.user.email,
                "otp": "123456",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)
        self.assertEqual(response.data["otp"][0], "Invalid or expired OTP.")

    @override_settings(RATELIMIT_ENABLE=False)
    def test_reset_password_otp_nonexistent_user(self):
        """Test password reset with nonexistent user."""
        response = self.client.post(
            self.reset_password_otp_url,
            {
                "email": "nonexistent@example.com",
                "otp": "123456",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(
            response.data["email"][0], "User with this email does not exist."
        )

    @override_settings(RATELIMIT_ENABLE=False)
    def test_reset_password_otp_password_mismatch(self):
        """Test password reset with mismatched passwords."""
        response = self.client.post(
            self.reset_password_otp_url,
            {
                "email": self.user.email,
                "otp": self.otp_code,
                "new_password": "newpassword123",
                "confirm_password": "differentpassword123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response.data)
        self.assertEqual(
            response.data["confirm_password"][0],
            "Password confirmation does not match.",
        )

    @override_settings(RATELIMIT_ENABLE=False)
    def test_reset_password_otp_same_as_current(self):
        """Test password reset with same password as current."""
        response = self.client.post(
            self.reset_password_otp_url,
            {
                "email": self.user.email,
                "otp": self.otp_code,
                "new_password": "oldpassword123",
                "confirm_password": "oldpassword123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)
        self.assertEqual(
            response.data["new_password"][0],
            "New password must be different from your current password.",
        )

    @override_settings(RATELIMIT_ENABLE=False)
    def test_reset_password_otp_weak_password(self):
        """Test password reset with weak password."""
        response = self.client.post(
            self.reset_password_otp_url,
            {
                "email": self.user.email,
                "otp": self.otp_code,
                "new_password": "123",
                "confirm_password": "123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_reset_password_otp_invalid_otp_format(self):
        """Test password reset with invalid OTP format."""
        test_cases = [
            "12345",
            "1234567",
            "12345a",
            "12345!",
            "",
        ]

        for invalid_otp in test_cases:
            with self.subTest(otp=invalid_otp):
                response = self.client.post(
                    self.reset_password_otp_url,
                    {
                        "email": self.user.email,
                        "otp": invalid_otp,
                        "new_password": "newpassword123",
                        "confirm_password": "newpassword123",
                    },
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("otp", response.data)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_reset_password_otp_missing_fields(self):
        """Test password reset with missing required fields."""
        test_cases = [
            {},
            {"email": self.user.email},
            {"email": self.user.email, "otp": self.otp_code},
            {
                "email": self.user.email,
                "otp": self.otp_code,
                "new_password": "newpass123",
            },
        ]

        for data in test_cases:
            with self.subTest(data=data):
                response = self.client.post(self.reset_password_otp_url, data)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_reset_password_otp_case_insensitive_email(self):
        """Test password reset with different email case."""
        response = self.client.post(
            self.reset_password_otp_url,
            {
                "email": self.user.email.upper(),
                "otp": self.otp_code,
                "new_password": "newpassword123",
                "confirm_password": "newpassword123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

    def test_reset_password_otp_user_model_method_availability(self):
        """Test that User model has required methods for OTP functionality."""

        self.assertTrue(hasattr(self.user, "verify_code"))
        self.assertTrue(callable(getattr(self.user, "verify_code", None)))

        is_valid = self.user.verify_code(self.otp_code)

        self.user.generate_verification_code()

    @override_settings(RATELIMIT_ENABLE=False)
    def test_reset_password_otp_multiple_attempts_with_same_otp(self):
        """Test that OTP can only be used once."""
        new_password = "newpassword123"

        response1 = self.client.post(
            self.reset_password_otp_url,
            {
                "email": self.user.email,
                "otp": self.otp_code,
                "new_password": new_password,
                "confirm_password": new_password,
            },
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(
            self.reset_password_otp_url,
            {
                "email": self.user.email,
                "otp": self.otp_code,
                "new_password": "anothernewpassword123",
                "confirm_password": "anothernewpassword123",
            },
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response2.data)
