"""
Test cases for OTPDeliveryService functionality.

Tests cover:
1. SMS delivery method
2. Email delivery method
3. Fallback from SMS to email
4. User validation for delivery methods
5. Delivery target display formatting
6. Error handling and logging
"""

import logging
from unittest.mock import patch, Mock, call
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService

User = get_user_model()


class OTPDeliveryServiceTestCase(TestCase):
    """Test cases for OTP delivery service."""

    def setUp(self):

        self.user_with_phone = User.objects.create_user(
            email="phone@example.com",
            password="password123",
            fullname="Phone User",
            phone_number="+1234567890",
            username="phoneuser",
        )

        self.user_without_phone = User.objects.create_user(
            email="nophone@example.com",
            password="password123",
            fullname="No Phone User",
            username="nophoneuser",
        )

        self.user_no_contacts = User.objects.create_user(
            email="",
            password="password123",
            fullname="No Contacts User",
            username="nocontactsuser",
        )

    def tearDown(self):
        User.objects.all().delete()

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_get_delivery_method_sms(self):
        """Test that get_delivery_method returns SMS when configured."""
        self.assertEqual(OTPDeliveryService.get_delivery_method(), "sms")

    @override_settings(OTP_DELIVERY_METHOD="EMAIL")
    def test_get_delivery_method_email_case_insensitive(self):
        """Test that get_delivery_method handles case insensitive values."""
        self.assertEqual(OTPDeliveryService.get_delivery_method(), "email")

    @override_settings(OTP_DELIVERY_METHOD="")
    def test_get_delivery_method_default(self):
        """Test that get_delivery_method returns email as default."""
        self.assertEqual(OTPDeliveryService.get_delivery_method(), "email")

    @override_settings(OTP_DELIVERY_METHOD="invalid")
    def test_get_delivery_method_invalid_falls_back(self):
        """Test that invalid delivery method uses email fallback."""

        self.assertEqual(OTPDeliveryService.get_delivery_method(), "invalid")

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_sms_neons")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_send_otp_via_sms_success(self, mock_logger, mock_send_sms_neons):
        """Test successful SMS OTP delivery."""
        mock_send_sms_neons.return_value = True

        result = OTPDeliveryService.send_otp(self.user_with_phone, "123456", "login")

        self.assertTrue(result)
        mock_send_sms_neons.assert_called_once()
        call_args = mock_send_sms_neons.call_args[0]
        self.assertIn("123456", call_args[0])
        self.assertEqual(["+1234567890"], call_args[1])
        mock_logger.info.assert_called_with(
            f"OTP sent via Twilio SMS to +1234567890 for user {self.user_with_phone.email}"
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_sms_neons")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_sms_fallback_to_email(self, mock_logger, mock_email, mock_send_sms_neons):
        """Test fallback from SMS to email when SMS service fails."""
        mock_send_sms_neons.return_value = False
        mock_email.delay = Mock()

        result = OTPDeliveryService.send_otp(self.user_with_phone, "123456", "login")

        self.assertTrue(result)
        mock_send_sms_neons.assert_called_once()
        mock_email.delay.assert_called_once()
        mock_logger.error.assert_called()

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_sms_neons")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_sms_fallback_to_vonage(self, mock_logger, mock_email, mock_sms_neons):
        """Test fallback from SMS to email when SMS service fails."""

        mock_sms_neons.return_value = False
        mock_email.delay = Mock()

        result = OTPDeliveryService.send_otp(self.user_with_phone, "123456", "login")

        self.assertTrue(result)
        mock_sms_neons.assert_called_once()
        mock_email.delay.assert_called_once()

        mock_logger.error.assert_called()

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_sms_delivery_no_phone_number(self, mock_logger):
        """Test SMS delivery fails gracefully when user has no phone number."""
        result = OTPDeliveryService.send_otp(self.user_without_phone, "123456", "login")

        self.assertFalse(result)
        mock_logger.error.assert_called_with(
            f"User {self.user_without_phone.email} has no phone number for SMS OTP delivery"
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_phone_number_formatting(self):
        """Test phone number formatting for SMS delivery."""

        user_no_plus = User.objects.create_user(
            email="noplus@example.com",
            password="password123",
            fullname="No Plus User",
            phone_number="01234567890",
            username="noplususer",
        )

        with patch(
            "apps.accounts.auth.services.otp_delivery_service.send_sms_neons"
        ) as mock_sms_neons:
            mock_sms_neons.return_value = True

            OTPDeliveryService.send_otp(user_no_plus, "123456", "login")

            call_args = mock_sms_neons.call_args[0]
            self.assertEqual(["+1234567890"], call_args[1])

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_send_otp_via_email_login(self, mock_logger, mock_email):
        """Test email OTP delivery for login."""
        mock_email.delay = Mock()

        result = OTPDeliveryService.send_otp(self.user_with_phone, "123456", "login")

        self.assertTrue(result)
        mock_email.delay.assert_called_once()
        call_args = mock_email.delay.call_args[1]
        self.assertEqual("Your Login OTP Code", call_args["subject"])
        self.assertIn("123456", call_args["text_content"])
        self.assertEqual(self.user_with_phone.email, call_args["to_email"])

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    def test_send_otp_via_email_password_reset(self, mock_email):
        """Test email OTP delivery for password reset."""
        mock_email.delay = Mock()

        result = OTPDeliveryService.send_otp(
            self.user_with_phone, "123456", "password_reset"
        )

        self.assertTrue(result)
        call_args = mock_email.delay.call_args[1]
        self.assertEqual("Password Reset OTP Code", call_args["subject"])
        self.assertIn("password reset", call_args["text_content"].lower())

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    def test_send_otp_via_email_verification(self, mock_email):
        """Test email OTP delivery for verification."""
        mock_email.delay = Mock()

        result = OTPDeliveryService.send_otp(
            self.user_with_phone, "123456", "verification"
        )

        self.assertTrue(result)
        call_args = mock_email.delay.call_args[1]
        self.assertEqual("Email Verification OTP Code", call_args["subject"])
        self.assertIn("verification", call_args["text_content"].lower())

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_email_delivery_failure(self, mock_logger, mock_email):
        """Test email delivery failure handling."""
        mock_email.delay.side_effect = Exception("Email service unavailable")

        result = OTPDeliveryService.send_otp(self.user_with_phone, "123456", "login")

        self.assertFalse(result)
        mock_logger.error.assert_called()

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_validate_user_for_sms_delivery_success(self):
        """Test user validation for SMS delivery with valid phone."""
        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_with_phone
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_validate_user_for_sms_delivery_no_phone(self):
        """Test user validation for SMS delivery without phone."""
        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_without_phone
        )
        self.assertFalse(is_valid)
        self.assertIn("Phone number is required", error)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_validate_user_for_email_delivery_success(self):
        """Test user validation for email delivery with valid email."""
        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_with_phone
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_validate_user_for_email_delivery_no_email(self):
        """Test user validation for email delivery without email."""
        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_no_contacts
        )
        self.assertFalse(is_valid)
        self.assertIn("Email address is required", error)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_get_delivery_target_display_sms(self):
        """Test delivery target display formatting for SMS."""
        display = OTPDeliveryService.get_delivery_target_display(self.user_with_phone)

        self.assertIn("SMS to", display)
        self.assertIn("+123", display)
        self.assertIn("7890", display)
        self.assertIn("*", display)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_get_delivery_target_display_email(self):
        """Test delivery target display formatting for email."""
        display = OTPDeliveryService.get_delivery_target_display(self.user_with_phone)

        self.assertIn("email to", display)
        self.assertIn("ph", display)
        self.assertIn("*", display)
        self.assertIn(".com", display)

    def test_get_delivery_target_display_short_phone(self):
        """Test delivery target display with short phone number."""
        short_user = User.objects.create_user(
            email="short@example.com",
            password="password123",
            phone_number="123",
            username="shortuser",
        )

        with override_settings(OTP_DELIVERY_METHOD="sms"):
            display = OTPDeliveryService.get_delivery_target_display(short_user)

            self.assertIn("SMS to ***", display)

    def test_get_delivery_target_display_short_email_username(self):
        """Test delivery target display with short email username."""
        short_email_user = User.objects.create_user(
            email="ab@example.com",
            password="password123",
            username="shortuser",
        )

        with override_settings(OTP_DELIVERY_METHOD="email"):
            display = OTPDeliveryService.get_delivery_target_display(short_email_user)

            self.assertIn("email to", display)
            self.assertIn("**@", display)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_sms_neons")
    def test_sms_message_content_login(self, mock_sms_neons):
        """Test SMS message content for different OTP types."""
        mock_sms_neons.return_value = True

        OTPDeliveryService.send_otp(self.user_with_phone, "123456", "login")

        call_args = mock_sms_neons.call_args[0]
        message = call_args[0]
        self.assertIn("kolct login otp code", message.lower())
        self.assertIn("123456", message)
        self.assertIn("10 minutes", message)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_sms_neons")
    def test_sms_message_content_password_reset(self, mock_sms_neons):
        """Test SMS message content for password reset."""
        mock_sms_neons.return_value = True

        OTPDeliveryService.send_otp(self.user_with_phone, "123456", "password_reset")

        call_args = mock_sms_neons.call_args[0]
        message = call_args[0]
        self.assertIn("kolct password reset otp code", message.lower())
        self.assertIn("123456", message)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_sms_neons")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_sms_exception_handling(self, mock_logger, mock_sms_neons):
        """Test SMS delivery exception handling."""
        mock_sms_neons.side_effect = Exception("SMS service error")

        with patch.object(
            OTPDeliveryService, "_send_otp_via_email"
        ) as mock_email_fallback:
            mock_email_fallback.return_value = True

            result = OTPDeliveryService.send_otp(
                self.user_with_phone, "123456", "login"
            )

            self.assertTrue(result)
            mock_logger.error.assert_called()
            mock_email_fallback.assert_called_once()

    def test_otp_type_parameter_validation(self):
        """Test that different OTP types are handled correctly."""
        valid_types = ["login", "password_reset", "verification"]

        for otp_type in valid_types:
            with self.subTest(otp_type=otp_type):
                with patch(
                    "apps.accounts.auth.services.otp_delivery_service.send_activation_email"
                ) as mock_email:
                    mock_email.delay = Mock()

                    with override_settings(OTP_DELIVERY_METHOD="email"):
                        result = OTPDeliveryService.send_otp(
                            self.user_with_phone, "123456", otp_type
                        )

                        self.assertTrue(result)
                        mock_email.delay.assert_called_once()

    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_logging_behavior(self, mock_logger):
        """Test that appropriate logging occurs for different scenarios."""

        with patch(
            "apps.accounts.auth.services.otp_delivery_service.send_sms_neons"
        ) as mock_sms:
            mock_sms.return_value = True

            with override_settings(OTP_DELIVERY_METHOD="sms"):
                OTPDeliveryService.send_otp(self.user_with_phone, "123456", "login")

                mock_logger.info.assert_called()
                log_message = mock_logger.info.call_args[0][0]
                self.assertIn("OTP sent via Twilio SMS", log_message)

        mock_logger.reset_mock()

        with patch(
            "apps.accounts.auth.services.otp_delivery_service.send_activation_email"
        ) as mock_email:
            mock_email.delay = Mock()

            with override_settings(OTP_DELIVERY_METHOD="email"):
                OTPDeliveryService.send_otp(self.user_with_phone, "123456", "login")

                mock_logger.info.assert_called()
                log_message = mock_logger.info.call_args[0][0]
                self.assertIn("OTP sent via email", log_message)
