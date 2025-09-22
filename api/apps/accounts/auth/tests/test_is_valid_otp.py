from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from apps.accounts.auth.models import OTP

User = get_user_model()


class IsValidOTPTests(TestCase):
    """
    Test suite for OTP validation endpoint that checks validity without consumption.
    """

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.is_valid_otp_url = reverse("auth-is-valid-otp")

        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            fullname="Test User",
            username="testuser",
        )

    def tearDown(self):
        """Clean up after tests."""
        User.objects.all().delete()
        OTP.objects.all().delete()

    @override_settings(RATELIMIT_ENABLE=False)
    def test_is_valid_otp_success_valid_otp(self):
        """Test successful validation of a valid OTP."""

        otp_code = self.user.generate_verification_code()

        response = self.client.post(
            self.is_valid_otp_url, {"email": self.user.email, "otp": otp_code}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("is_valid", response.data)
        self.assertIn("message", response.data)
        self.assertTrue(response.data["is_valid"])
        self.assertEqual(response.data["message"], "OTP is valid.")

        self.assertTrue(OTP.objects.filter(user=self.user, code=otp_code).exists())

    @override_settings(RATELIMIT_ENABLE=False)
    def test_is_valid_otp_success_invalid_otp(self):
        """Test validation of an invalid OTP."""

        self.user.generate_verification_code()

        response = self.client.post(
            self.is_valid_otp_url, {"email": self.user.email, "otp": "123456"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)
        self.assertEqual(response.data["otp"][0], "Invalid or expired OTP.")

    @override_settings(RATELIMIT_ENABLE=False)
    def test_is_valid_otp_expired_otp(self):
        """Test validation of an expired OTP."""

        expired_time = timezone.now() - timezone.timedelta(minutes=15)
        OTP.objects.create(user=self.user, code="123456", expires_at=expired_time)

        response = self.client.post(
            self.is_valid_otp_url, {"email": self.user.email, "otp": "123456"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)
        self.assertEqual(response.data["otp"][0], "Invalid or expired OTP.")

    @override_settings(RATELIMIT_ENABLE=False)
    def test_is_valid_otp_nonexistent_user(self):
        """Test validation with nonexistent user."""
        response = self.client.post(
            self.is_valid_otp_url, {"email": "nonexistent@example.com", "otp": "123456"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(
            response.data["email"][0], "User with this email does not exist."
        )

    @override_settings(RATELIMIT_ENABLE=False)
    def test_is_valid_otp_invalid_email_format(self):
        """Test validation with invalid email format."""
        response = self.client.post(
            self.is_valid_otp_url, {"email": "invalid-email", "otp": "123456"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_is_valid_otp_invalid_otp_format(self):
        """Test validation with invalid OTP format."""
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
                    self.is_valid_otp_url,
                    {"email": self.user.email, "otp": invalid_otp},
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("otp", response.data)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_is_valid_otp_missing_fields(self):
        """Test validation with missing required fields."""
        test_cases = [
            {},
            {"email": self.user.email},
            {"otp": "123456"},
        ]

        for data in test_cases:
            with self.subTest(data=data):
                response = self.client.post(self.is_valid_otp_url, data)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_is_valid_otp_case_insensitive_email(self):
        """Test validation with different email case."""

        otp_code = self.user.generate_verification_code()

        response = self.client.post(
            self.is_valid_otp_url, {"email": self.user.email.upper(), "otp": otp_code}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_valid"])

    @override_settings(RATELIMIT_ENABLE=False)
    def test_is_valid_otp_no_otp_exists(self):
        """Test validation when no OTP exists for user."""
        response = self.client.post(
            self.is_valid_otp_url, {"email": self.user.email, "otp": "123456"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)
        self.assertEqual(response.data["otp"][0], "Invalid or expired OTP.")

    def test_is_valid_otp_user_model_method_availability(self):
        """Test that User model has required methods for OTP validation."""

        self.assertTrue(hasattr(self.user, "is_otp_valid"))
        self.assertTrue(callable(getattr(self.user, "is_otp_valid", None)))

        otp_code = self.user.generate_verification_code()
        is_valid = self.user.is_otp_valid(otp_code)
        self.assertTrue(is_valid)

        is_valid = self.user.is_otp_valid("999999")
        self.assertFalse(is_valid)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_is_valid_otp_multiple_validations_same_otp(self):
        """Test that OTP can be validated multiple times without consumption."""

        otp_code = self.user.generate_verification_code()

        response1 = self.client.post(
            self.is_valid_otp_url, {"email": self.user.email, "otp": otp_code}
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertTrue(response1.data["is_valid"])

        response2 = self.client.post(
            self.is_valid_otp_url, {"email": self.user.email, "otp": otp_code}
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertTrue(response2.data["is_valid"])

        self.assertTrue(OTP.objects.filter(user=self.user, code=otp_code).exists())

    @override_settings(RATELIMIT_ENABLE=False)
    def test_is_valid_otp_multiple_users(self):
        """Test OTP validation for multiple users."""

        user2 = User.objects.create_user(
            email="test2@example.com",
            password="testpassword123",
            fullname="Test User 2",
            username="testuser2",
        )

        otp1 = self.user.generate_verification_code()
        otp2 = user2.generate_verification_code()

        response1 = self.client.post(
            self.is_valid_otp_url, {"email": self.user.email, "otp": otp1}
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertTrue(response1.data["is_valid"])

        response2 = self.client.post(
            self.is_valid_otp_url, {"email": user2.email, "otp": otp2}
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertTrue(response2.data["is_valid"])

        response3 = self.client.post(
            self.is_valid_otp_url, {"email": self.user.email, "otp": otp2}
        )
        self.assertEqual(response3.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_is_valid_otp_state_preservation(self):
        """Test that OTP validation doesn't change OTP state."""

        otp_code = self.user.generate_verification_code()
        original_otp = OTP.objects.get(user=self.user, code=otp_code)
        original_created_at = original_otp.created_at
        original_expires_at = original_otp.expires_at

        response = self.client.post(
            self.is_valid_otp_url, {"email": self.user.email, "otp": otp_code}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_valid"])

        updated_otp = OTP.objects.get(user=self.user, code=otp_code)
        self.assertEqual(updated_otp.created_at, original_created_at)
        self.assertEqual(updated_otp.expires_at, original_expires_at)
        self.assertEqual(updated_otp.code, otp_code)
