"""
SMS OTP Registration Integration Tests

This test suite verifies that SMS OTP delivery works correctly for user registration
when OTP_DELIVERY_METHOD=sms is configured, with NO fallback to email.

Key behaviors tested:
1. SMS-only delivery when configured
2. No fallback to email when SMS fails
3. Phone number validation and formatting
4. Registration flow with SMS OTP verification
5. Error handling for missing phone numbers
6. Integration with Neons SMS service
"""

import pytest
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService
from apps.accounts.auth.serializers.register import RegisterSerializer
from apps.accounts.auth.models import OTP
from apps.accounts.user.models import VerificationCode

User = get_user_model()


class SMSOTPRegistrationIntegrationTestCase(APITestCase):
    """Test SMS OTP registration integration with strict SMS-only delivery."""

    def setUp(self):
        """Set up test data."""

        User.objects.all().delete()
        OTP.objects.all().delete()
        VerificationCode.objects.all().delete()

    def tearDown(self):
        """Clean up test data."""
        User.objects.all().delete()
        OTP.objects.all().delete()
        VerificationCode.objects.all().delete()

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_register_with_sms_delivery_success(self, mock_sms_task):
        """Test successful user registration with SMS OTP delivery."""
        mock_sms_task.return_value = True

        registration_data = {
            "email": "test@example.com",
            "fullname": "Test User",
            "password": "securepassword123",
            "phone_number": "+21626716816",
        }

        response = self.client.post(
            "/api/v1/auth/register/", registration_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn("user registered successfully", response.data["message"].lower())
        self.assertIn(
            "please verify to complete registration", response.data["message"].lower()
        )

        user = User.objects.get(email="test@example.com")
        self.assertEqual(user.phone_number, "+21626716816")
        self.assertEqual(user.fullname, "Test User")

        self.assertFalse(user.is_email_verified)

        otp = OTP.objects.get(user=user)
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp.code), 6)

        mock_sms_task.assert_called_once()
        call_args = mock_sms_task.call_args[0]
        message, phone_numbers, otp_type = call_args

        self.assertIn(otp.code, message)
        self.assertEqual(["+21626716816"], phone_numbers)
        self.assertEqual("registration", otp_type)
        self.assertIn("Welcome to Kolct", message)

    @override_settings(OTP_DELIVERY_METHOD="sms", SMS_FALLBACK_TO_EMAIL=False)
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_register_with_sms_delivery_failure_no_fallback(self, mock_sms_task):
        """Test registration fails when SMS delivery fails and no fallback."""
        mock_sms_task.return_value = False

        registration_data = {
            "email": "test@example.com",
            "fullname": "Test User",
            "password": "securepassword123",
            "phone_number": "+21626716816",
        }

        response = self.client.post(
            "/api/v1/auth/register/", registration_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Failed to send verification code", str(response.data))

        self.assertFalse(User.objects.filter(email="test@example.com").exists())

        self.assertEqual(OTP.objects.count(), 0)

        mock_sms_task.assert_called_once()

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_register_without_phone_number_fails(self):
        """Test registration fails when SMS is configured but no phone number provided."""
        registration_data = {
            "email": "test@example.com",
            "fullname": "Test User",
            "password": "securepassword123",
        }

        response = self.client.post(
            "/api/v1/auth/register/", registration_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error_data = response.data.get("error", response.data)
        self.assertIn("phone_number", error_data)

        self.assertFalse(User.objects.filter(email="test@example.com").exists())

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_phone_number_formatting_with_country_code(self, mock_sms_task):
        """Test that phone numbers without + are properly formatted."""
        mock_sms_task.return_value = True

        registration_data = {
            "email": "test@example.com",
            "fullname": "Test User",
            "password": "securepassword123",
            "phone_number": "21626716816",
        }

        response = self.client.post(
            "/api/v1/auth/register/", registration_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_sms_task.assert_called_once()
        call_args = mock_sms_task.call_args[0]
        message, phone_numbers, otp_type = call_args

        self.assertEqual(["+21626716816"], phone_numbers)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_register_serializer_sms_validation(self, mock_sms_task):
        """Test RegisterSerializer validation with SMS delivery method."""
        mock_sms_task.return_value = True

        valid_data = {
            "email": "test@example.com",
            "fullname": "Test User",
            "password": "securepassword123",
            "phone_number": "+21626716816",
        }

        serializer = RegisterSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        self.assertTrue(OTP.objects.filter(user=user).exists())
        mock_sms_task.assert_called_once()

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_register_serializer_missing_phone_validation(self):
        """Test RegisterSerializer fails validation when SMS is configured but phone missing."""

        invalid_data = {
            "email": "test@example.com",
            "fullname": "Test User",
            "password": "securepassword123",
        }

        serializer = RegisterSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_duplicate_phone_number_validation(self):
        """Test that duplicate phone numbers are rejected."""

        User.objects.create_user(
            email="first@example.com",
            password="password123",
            fullname="First User",
            phone_number="+21626716816",
        )

        duplicate_data = {
            "email": "second@example.com",
            "fullname": "Second User",
            "password": "securepassword123",
            "phone_number": "+21626716816",
        }

        response = self.client.post(
            "/api/v1/auth/register/", duplicate_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error_data = response.data.get("error", response.data)
        self.assertIn("phone_number", error_data)


class SMSOTPDeliveryServiceTestCase(TestCase):
    """Test OTPDeliveryService SMS-only behavior."""

    def setUp(self):
        """Set up test data."""
        self.user_with_phone = User.objects.create_user(
            email="with_phone@example.com",
            password="password123",
            fullname="User With Phone",
            phone_number="+21626716816",
            username="withphone",
        )

        self.user_without_phone = User.objects.create_user(
            email="no_phone@example.com",
            password="password123",
            fullname="User Without Phone",
            username="nophone",
        )

    def tearDown(self):
        """Clean up test data."""
        User.objects.all().delete()

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_get_delivery_method_returns_sms(self):
        """Test that delivery method returns 'sms' when configured."""
        delivery_method = OTPDeliveryService.get_delivery_method()
        self.assertEqual(delivery_method, "sms")

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_send_otp_sms_success(self, mock_sms_task):
        """Test successful SMS OTP sending."""
        mock_sms_task.return_value = True

        result = OTPDeliveryService.send_otp(
            self.user_with_phone, "123456", "registration"
        )

        self.assertTrue(result)
        mock_sms_task.assert_called_once()

        call_args = mock_sms_task.call_args[0]
        message, phone_numbers, otp_type = call_args

        self.assertIn("123456", message)
        self.assertEqual(["+21626716816"], phone_numbers)
        self.assertEqual("registration", otp_type)

    @override_settings(OTP_DELIVERY_METHOD="sms", SMS_FALLBACK_TO_EMAIL=False)
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_send_otp_sms_failure_no_fallback(self, mock_sms_task):
        """Test SMS failure with no email fallback."""
        mock_sms_task.return_value = False

        result = OTPDeliveryService.send_otp(
            self.user_with_phone, "123456", "registration"
        )

        self.assertFalse(result)
        mock_sms_task.assert_called_once()

    @override_settings(OTP_DELIVERY_METHOD="sms", SMS_FALLBACK_TO_EMAIL=False)
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    def test_send_otp_no_phone_number_no_fallback(self, mock_email):
        """Test SMS delivery fails when user has no phone and no fallback occurs."""
        mock_email.delay = Mock()

        result = OTPDeliveryService.send_otp(
            self.user_without_phone, "123456", "registration"
        )

        self.assertFalse(result)
        mock_email.delay.assert_not_called()

    @override_settings(OTP_DELIVERY_METHOD="sms", SMS_FALLBACK_TO_EMAIL=False)
    def test_validate_user_requires_phone_number(self):
        """Test user validation requires phone number when SMS is configured."""

        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_with_phone
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_without_phone
        )
        self.assertFalse(is_valid)
        self.assertIn("Phone number is required", error)

    @override_settings(OTP_DELIVERY_METHOD="sms", SMS_FALLBACK_TO_EMAIL=False)
    def test_get_delivery_target_display_sms_only(self):
        """Test delivery target display for SMS-only mode."""

        display = OTPDeliveryService.get_delivery_target_display(self.user_with_phone)
        self.assertIn("SMS to", display)
        self.assertIn("+216", display)

        display = OTPDeliveryService.get_delivery_target_display(
            self.user_without_phone
        )
        self.assertIn("SMS", display)
        self.assertIn("not available", display)

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    def test_email_delivery_when_configured(self, mock_email):
        """Test that email delivery works when email method is configured."""
        mock_email.delay = Mock()

        result = OTPDeliveryService.send_otp(
            self.user_with_phone, "123456", "registration"
        )

        self.assertTrue(result)
        mock_email.delay.assert_called_once()

        call_args = mock_email.delay.call_args[1]
        self.assertIn("123456", call_args["text_content"])
        self.assertEqual("with_phone@example.com", call_args["to_email"])


class SMSOTPMessageFormattingTestCase(TestCase):
    """Test SMS message formatting for different OTP types."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            fullname="Test User",
            phone_number="+21626716816",
            username="testuser",
        )

    def tearDown(self):
        """Clean up test data."""
        User.objects.all().delete()

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_registration_otp_message_format(self, mock_sms_task):
        """Test registration OTP message formatting."""
        mock_sms_task.return_value = True

        OTPDeliveryService.send_otp(self.user, "123456", "registration")

        mock_sms_task.assert_called_once()
        message = mock_sms_task.call_args[0][0]

        self.assertIn("Welcome to Kolct!", message)
        self.assertIn("123456", message)
        self.assertIn("registration OTP code", message)
        self.assertIn("10 minutes", message)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_verification_otp_message_format(self, mock_sms_task):
        """Test verification OTP message formatting."""
        mock_sms_task.return_value = True

        OTPDeliveryService.send_otp(self.user, "654321", "verification")

        mock_sms_task.assert_called_once()
        message = mock_sms_task.call_args[0][0]

        self.assertIn("654321", message)
        self.assertIn("verification OTP code", message)
        self.assertIn("10 minutes", message)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_login_otp_message_format(self, mock_sms_task):
        """Test login OTP message formatting."""
        mock_sms_task.return_value = True

        OTPDeliveryService.send_otp(self.user, "789012", "login")

        mock_sms_task.assert_called_once()
        message = mock_sms_task.call_args[0][0]

        self.assertIn("789012", message)
        self.assertIn("login OTP code", message)
        self.assertIn("10 minutes", message)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_password_reset_otp_message_format(self, mock_sms_task):
        """Test password reset OTP message formatting."""
        mock_sms_task.return_value = True

        OTPDeliveryService.send_otp(self.user, "456789", "password_reset")

        mock_sms_task.assert_called_once()
        message = mock_sms_task.call_args[0][0]

        self.assertIn("456789", message)
        self.assertIn("password reset OTP code", message)
        self.assertIn("10 minutes", message)
