from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from apps.accounts.auth.models import OTP

User = get_user_model()


class ForgotPasswordOTPTests(TestCase):
    """
    Test suite for forgot password OTP functionality.
    """

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.forgot_password_otp_url = reverse("auth-forgot-password-otp")

        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            fullname="Test User",
            username="testuser",
            phone_number="+1234567894",
        )

    def tearDown(self):
        """Clean up after tests."""
        User.objects.all().delete()
        OTP.objects.all().delete()

    @override_settings(RATELIMIT_ENABLE=False, OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_forgot_password_otp_success(self, mock_sms_task):
        """Test successful password reset OTP request."""
        mock_sms_task.return_value = MagicMock()

        response = self.client.post(
            self.forgot_password_otp_url, {"email": self.user.email}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        self.assertIn("SMS to", response.data["message"])

        self.assertTrue(OTP.objects.filter(user=self.user).exists())
        otp = OTP.objects.filter(user=self.user).latest("created_at")
        self.assertEqual(len(otp.code), 6)
        self.assertTrue(otp.code.isdigit())

    @override_settings(RATELIMIT_ENABLE=False)
    def test_forgot_password_otp_nonexistent_user(self):
        """Test password reset OTP request with nonexistent user."""
        response = self.client.post(
            self.forgot_password_otp_url, {"email": "nonexistent@example.com"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(
            response.data["email"][0], "User with this email does not exist."
        )

        self.assertFalse(OTP.objects.exists())

    @override_settings(RATELIMIT_ENABLE=False)
    def test_forgot_password_otp_invalid_email(self):
        """Test password reset OTP request with invalid email format."""
        response = self.client.post(
            self.forgot_password_otp_url, {"email": "invalid-email"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_forgot_password_otp_missing_email(self):
        """Test password reset OTP request without email."""
        response = self.client.post(self.forgot_password_otp_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    @override_settings(RATELIMIT_ENABLE=False)
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_forgot_password_otp_case_insensitive_email(self, mock_sms_task):
        """Test password reset OTP request with different email case."""
        mock_sms_task.return_value = MagicMock()

        response = self.client.post(
            self.forgot_password_otp_url, {"email": self.user.email.upper()}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        self.assertTrue(OTP.objects.filter(user=self.user).exists())

    @override_settings(RATELIMIT_ENABLE=False, OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_forgot_password_otp_sms_sending(self, mock_sms_task):
        """Test that password reset OTP SMS is sent correctly."""
        mock_sms_task.return_value = MagicMock()

        response = self.client.post(
            self.forgot_password_otp_url, {"email": self.user.email}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_sms_task.assert_called_once()
        call_args = mock_sms_task.call_args

        message = call_args[0][0]
        phone_numbers = call_args[0][1]
        otp_type = call_args[0][2]

        self.assertIn("password reset", message.lower())
        self.assertEqual(phone_numbers, [self.user.phone_number])
        self.assertEqual(otp_type, "password_reset")

    @override_settings(RATELIMIT_ENABLE=False)
    def test_forgot_password_otp_replaces_existing_otp(self):
        """Test that new OTP request replaces existing OTP."""

        initial_response = self.client.post(
            self.forgot_password_otp_url, {"email": self.user.email}
        )
        self.assertEqual(initial_response.status_code, status.HTTP_200_OK)

        initial_otp = OTP.objects.filter(user=self.user).latest("created_at")
        initial_code = initial_otp.code

        new_response = self.client.post(
            self.forgot_password_otp_url, {"email": self.user.email}
        )
        self.assertEqual(new_response.status_code, status.HTTP_200_OK)

        new_otp = OTP.objects.filter(user=self.user).latest("created_at")
        self.assertNotEqual(initial_code, new_otp.code)

    def test_forgot_password_otp_user_model_method_availability(self):
        """Test that User model has required methods for OTP functionality."""

        self.assertTrue(hasattr(self.user, "generate_verification_code"))
        self.assertTrue(
            callable(getattr(self.user, "generate_verification_code", None))
        )

        self.assertTrue(hasattr(self.user, "send_verification_email"))
        self.assertTrue(callable(getattr(self.user, "send_verification_email", None)))

        code = self.user.generate_verification_code()
        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    @override_settings(RATELIMIT_ENABLE=False)
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_forgot_password_otp_multiple_users(self, mock_sms_task):
        """Test password reset OTP for multiple users."""
        mock_sms_task.return_value = MagicMock()

        user2 = User.objects.create_user(
            email="test2@example.com",
            password="testpassword123",
            fullname="Test User 2",
            username="testuser2",
            phone_number="+1234567895",
        )

        response1 = self.client.post(
            self.forgot_password_otp_url, {"email": self.user.email}
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(
            self.forgot_password_otp_url, {"email": user2.email}
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        self.assertTrue(OTP.objects.filter(user=self.user).exists())
        self.assertTrue(OTP.objects.filter(user=user2).exists())

        otp1 = OTP.objects.filter(user=self.user).latest("created_at")
        otp2 = OTP.objects.filter(user=user2).latest("created_at")
        self.assertNotEqual(otp1.code, otp2.code)
