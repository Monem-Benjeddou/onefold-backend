"""
Test registration OTP delivery based on OTP_DELIVERY_METHOD setting.

This test ensures that the registration flow respects the OTP_DELIVERY_METHOD
environment variable and sends OTPs via the correct channel (SMS or email).
"""

from unittest.mock import patch, Mock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status


User = get_user_model()


class RegistrationOTPDeliveryTestCase(TestCase):
    """Test OTP delivery method in registration flow."""

    def setUp(self):
        self.client = APIClient()
        self.registration_data = {
            "email": "test@example.com",
            "fullname": "Test User",
            "password": "testpass123",
            "phone_number": "+21626716816",
        }
        self.resend_data = {"email": "test@example.com"}

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_registration_respects_sms_setting_uses_sms(self, mock_send_otp):
        """Test that registration respects SMS setting and uses SMS delivery."""
        mock_send_otp.return_value = True

        response = self.client.post("/api/v1/auth/register/", self.registration_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_send_otp.assert_called_once()
        call_args = mock_send_otp.call_args

        user = call_args[0][0]
        otp_code = call_args[0][1]
        otp_type = call_args[0][2]

        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(len(otp_code), 6)
        self.assertEqual(otp_type, "registration")

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    def test_registration_uses_email_when_email_configured(self, mock_send_email):
        """Test that registration uses email delivery when OTP_DELIVERY_METHOD=email."""
        mock_send_email.delay.return_value = Mock()

        response = self.client.post("/api/v1/auth/register/", self.registration_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_send_email.delay.assert_called_once()

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    def test_registration_uses_email_verification_when_email_configured(
        self, mock_send_email
    ):
        """Test that registration uses email verification when OTP_DELIVERY_METHOD=email."""
        mock_send_email.delay.return_value = Mock()

        response = self.client.post("/api/v1/auth/register/", self.registration_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_send_email.delay.assert_called_once()
        call_args = mock_send_email.delay.call_args

        subject = call_args[1]["subject"]
        to_email = call_args[1]["to_email"]

        self.assertIn("Welcome to Kolct", subject)
        self.assertEqual(to_email, "test@example.com")

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_registration_sms_setting_uses_sms_delivery(self, mock_send_otp):
        """Test that registration uses SMS delivery when OTP_DELIVERY_METHOD=sms."""
        mock_send_otp.return_value = True

        response = self.client.post("/api/v1/auth/register/", self.registration_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_send_otp.assert_called_once()
        call_args = mock_send_otp.call_args

        user = call_args[0][0]
        otp_code = call_args[0][1]
        otp_type = call_args[0][2]

        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(len(otp_code), 6)
        self.assertEqual(otp_type, "registration")

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_sms_otp"
    )
    def test_resend_verification_code_uses_sms_delivery(self, mock_send_sms_otp):
        """Test that resend verification code uses SMS delivery when phone_number is provided."""
        mock_send_sms_otp.return_value = True

        from apps.accounts.auth.models import OTP

        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            fullname="Test User",
            phone_number="+1234567890",
            username="testuser",
        )
        OTP.objects.create(user=user, code="123456")

        response = self.client.post(
            "/api/v1/auth/resend-verification-code/", {"phone_number": "+1234567890"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_sms_otp.assert_called_once()

        call_args = mock_send_sms_otp.call_args
        called_user = call_args[0][0]
        otp_code = call_args[0][1]
        otp_type = call_args[0][2]

        self.assertEqual(called_user.email, "test@example.com")
        self.assertEqual(len(otp_code), 6)
        self.assertEqual(otp_type, "registration")

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    def test_registration_creates_verification_code(self, mock_send_email):
        """Test that registration creates an OTP record (unified approach)."""
        mock_send_email.delay.return_value = Mock()

        response = self.client.post("/api/v1/auth/register/", self.registration_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="test@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(user.phone_number, "+21626716816")

        from apps.accounts.auth.models import OTP

        otp = OTP.objects.get(user=user)
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp.code), 6)
        self.assertEqual(otp.purpose, "registration")

        mock_send_email.delay.assert_called_once()

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_registration_validates_phone_number_for_sms(self):
        """Test that registration validates phone number when SMS delivery is configured."""

        invalid_data = self.registration_data.copy()
        invalid_data["phone_number"] = ""

        response = self.client.post("/api/v1/auth/register/", invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data.get("error", {}))

    def test_registration_response_structure(self):
        """Test that registration response has the correct structure."""
        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp",
            return_value=True,
        ):
            response = self.client.post(
                "/api/v1/auth/register/", self.registration_data
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_data = response.data
        self.assertIn("message", response_data)
        self.assertIn("user", response_data)

        self.assertNotIn("refresh", response_data)
        self.assertNotIn("access", response_data)

        user_data = response_data["user"]
        self.assertEqual(user_data["email"], "test@example.com")
        self.assertEqual(user_data["fullname"], "Test User")
