from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.auth.models import OTP
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class VerifyRegistrationOTPViewTestCase(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()
        self.verify_url = "/api/v1/auth/verify-registration-otp/"

        self.user = User.objects.create_user(
            email="unverified@example.com",
            password="password123",
            fullname="Unverified User",
            username="unverified",
            phone_number="+1234567890",
            is_active=False,
            is_email_verified=False,
        )

        self.valid_otp = OTP.objects.create(
            user=self.user,
            code="123456",
            purpose="registration",
            is_used=False,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

    def test_verify_registration_otp_success_email(self):
        """Test successful registration OTP verification with email."""
        data = {"email": "unverified@example.com", "otp": "123456"}

        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("refresh", response.data)
        self.assertIn("access", response.data)
        self.assertIn("user", response.data)
        self.assertIn("message", response.data)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.is_phone_verified)
        self.assertTrue(self.user.is_verified)

        self.valid_otp.refresh_from_db()
        self.assertTrue(self.valid_otp.is_used)

    def test_verify_registration_otp_invalid_code(self):
        """Test verification with invalid OTP code."""
        data = {"email": "unverified@example.com", "otp": "000000"}

        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)

    def test_verify_registration_otp_expired(self):
        """Test verification with expired OTP."""

        expired_otp = OTP.objects.create(
            user=self.user,
            code="654321",
            purpose="registration",
            is_used=False,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        data = {"email": "unverified@example.com", "otp": "654321"}

        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)

    def test_verify_registration_otp_wrong_purpose(self):
        """Test verification with OTP of wrong purpose."""

        login_otp = OTP.objects.create(
            user=self.user,
            code="789012",
            purpose="login",
            is_used=False,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        data = {"email": "unverified@example.com", "otp": "789012"}

        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)

    def test_verify_registration_otp_already_used(self):
        """Test verification with already used OTP."""

        self.valid_otp.is_used = True
        self.valid_otp.save()

        data = {"email": "unverified@example.com", "otp": "123456"}

        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)

    def test_verify_registration_otp_nonexistent_user(self):
        """Test verification with non-existent user."""
        data = {"email": "nonexistent@example.com", "otp": "123456"}

        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_registration_otp_invalid_format(self):
        """Test verification with invalid OTP format."""
        data = {"email": "unverified@example.com", "otp": "12345"}

        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {"email": "unverified@example.com", "otp": "abcdef"}

        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_registration_enables_login(self):
        """Test that after successful verification, user can login."""

        data = {"email": "unverified@example.com", "otp": "123456"}
        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        login_data = {"email": "unverified@example.com", "password": "password123"}
        login_response = self.client.post("/api/v1/auth/login/", login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)

    def test_verify_registration_otp_success_phone_number(self):
        """Test successful registration OTP verification with phone number."""
        data = {"phone_number": "+1234567890", "otp": "123456"}

        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("refresh", response.data)
        self.assertIn("access", response.data)
        self.assertIn("user", response.data)
        self.assertIn("message", response.data)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.is_phone_verified)
        self.assertTrue(self.user.is_verified)

    def test_verify_registration_otp_both_fields_error(self):
        """Test that providing both email and phone number returns error."""
        data = {
            "email": "unverified@example.com",
            "phone_number": "+1234567890",
            "otp": "123456",
        }

        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Please provide either email or phone number, not both", str(response.data)
        )

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)
