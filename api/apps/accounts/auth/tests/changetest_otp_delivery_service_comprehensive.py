"""
Comprehensive test cases for OTPDeliveryService functionality.

Tests cover:
1. SMS delivery with Twilio and Vonage
2. Email delivery as primary and fallback method
3. OTP_DELIVERY_METHOD environment variable behavior
4. User validation for different delivery methods
5. Phone number formatting and validation
6. Error handling and fallback mechanisms
7. Message content for different OTP types
8. Privacy masking for delivery target display
9. Logging and monitoring behavior
10. Integration with external SMS services
"""

import logging
from unittest.mock import patch, Mock, MagicMock, call
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.conf import settings

from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService

User = get_user_model()


class OTPDeliveryServiceComprehensiveTestCase(TestCase):
    """Comprehensive test cases for OTP delivery service."""

    def setUp(self):

        self.user_full_contacts = User.objects.create_user(
            email="full@example.com",
            password="password123",
            fullname="Full Contact User",
            phone_number="+1234567890",
            username="fulluser",
        )

        self.user_email_only = User.objects.create_user(
            email="emailonly@example.com",
            password="password123",
            fullname="Email Only User",
            username="emailuser",
        )

        self.user_phone_only = User.objects.create_user(
            email="phoneonly@example.com",
            password="password123",
            fullname="Phone Only User",
            phone_number="+9876543210",
            username="phoneuser",
        )

        self.user_no_contacts = User.objects.create_user(
            email="nocontacts@example.com",
            password="password123",
            fullname="No Contacts User",
            username="nocontacts",
        )

        self.user_international_phone = User.objects.create_user(
            email="intl@example.com",
            password="password123",
            fullname="International User",
            phone_number="+44123456789",
            username="intluser",
        )

        self.user_unformatted_phone = User.objects.create_user(
            email="unformatted@example.com",
            password="password123",
            fullname="Unformatted Phone User",
            phone_number="01234567890",
            username="unformatteduser",
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_get_delivery_method_default(self):
        """Test default delivery method when OTP_DELIVERY_METHOD is not set."""
        with override_settings():
            if hasattr(settings, "OTP_DELIVERY_METHOD"):
                delattr(settings, "OTP_DELIVERY_METHOD")
            self.assertEqual(OTPDeliveryService.get_delivery_method(), "email")

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_get_delivery_method_sms(self):
        """Test SMS delivery method configuration."""
        self.assertEqual(OTPDeliveryService.get_delivery_method(), "sms")

    @override_settings(OTP_DELIVERY_METHOD="EMAIL")
    def test_get_delivery_method_email_case_insensitive(self):
        """Test email delivery method with case insensitivity."""
        self.assertEqual(OTPDeliveryService.get_delivery_method(), "email")

    @override_settings(OTP_DELIVERY_METHOD="")
    def test_get_delivery_method_empty_string(self):
        """Test empty string falls back to email."""
        self.assertEqual(OTPDeliveryService.get_delivery_method(), "email")

    @override_settings(OTP_DELIVERY_METHOD="invalid_method")
    def test_get_delivery_method_invalid(self):
        """Test invalid delivery method returns the invalid value (handled in send_otp)."""
        self.assertEqual(OTPDeliveryService.get_delivery_method(), "invalid_method")

    @override_settings(OTP_DELIVERY_METHOD="SMS")
    def test_get_delivery_method_case_conversion(self):
        """Test that get_delivery_method converts to lowercase."""
        self.assertEqual(OTPDeliveryService.get_delivery_method(), "sms")

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_sms_neons")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_sms_delivery_success_twilio(self, mock_logger, mock_send_sms):
        """Test successful SMS delivery using Twilio."""
        mock_send_sms.return_value = True

        result = OTPDeliveryService.send_otp(self.user_full_contacts, "123456", "login")

        self.assertTrue(result)
        mock_send_sms.assert_called_once()

        call_args = mock_send_sms.call_args[0]
        message, phone_numbers = call_args

        self.assertIn("123456", message)
        self.assertIn("kolct login otp code", message.lower())
        self.assertEqual(["+1234567890"], phone_numbers)

        mock_logger.info.assert_called_with(
            f"OTP sent via Twilio SMS to +1234567890 for user {self.user_full_contacts.email}"
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_sms_neons")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_sms_fallback_twilio_to_vonage(self, mock_logger, mock_neons):
        """Test SMS sending with Neons SMS service (handles fallback internally)."""
        mock_neons.return_value = True

        result = OTPDeliveryService.send_otp(self.user_full_contacts, "123456", "login")

        self.assertTrue(result)
        mock_neons.assert_called_once()

        call_args = mock_neons.call_args[0]
        message, phone_numbers = call_args
        self.assertIn("123456", message)
        self.assertEqual(["+1234567890"], phone_numbers)

        mock_logger.info.assert_called_with(
            f"OTP sent via Twilio SMS to +1234567890 for user {self.user_full_contacts.email}"
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_sms_neons")
    @patch.object(OTPDeliveryService, "_send_otp_via_email")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_sms_fallback_to_email(self, mock_logger, mock_email, mock_neons):
        """Test fallback from SMS to email when SMS service fails."""
        mock_neons.return_value = False
        mock_email.return_value = True

        result = OTPDeliveryService.send_otp(self.user_full_contacts, "123456", "login")

        self.assertTrue(result)
        mock_neons.assert_called_once()
        mock_email.assert_called_once_with(self.user_full_contacts, "123456", "login")

        mock_logger.error.assert_called_with(
            f"All SMS services failed for +1234567890, falling back to email"
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_sms_delivery_no_phone_number(self, mock_logger):
        """Test SMS delivery failure when user has no phone number."""
        result = OTPDeliveryService.send_otp(self.user_email_only, "123456", "login")

        self.assertFalse(result)
        mock_logger.error.assert_called_with(
            f"User {self.user_email_only.email} has no phone number for SMS OTP delivery"
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_sms_neons")
    def test_phone_number_formatting_add_plus(self, mock_sms):
        """Test phone number formatting - adding + prefix."""
        mock_sms.return_value = True

        result = OTPDeliveryService.send_otp(
            self.user_unformatted_phone, "123456", "login"
        )

        self.assertTrue(result)
        call_args = mock_sms.call_args[0]
        phone_numbers = call_args[1]

        self.assertEqual(["+1234567890"], phone_numbers)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_sms_neons")
    def test_phone_number_formatting_international(self, mock_sms):
        """Test phone number formatting with international numbers."""
        mock_sms.return_value = True

        result = OTPDeliveryService.send_otp(
            self.user_international_phone, "123456", "login"
        )

        self.assertTrue(result)
        call_args = mock_sms.call_args[0]
        phone_numbers = call_args[1]

        self.assertEqual(["+44123456789"], phone_numbers)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_sms_neons")
    @patch.object(OTPDeliveryService, "_send_otp_via_email")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_sms_exception_handling(self, mock_logger, mock_email, mock_sms):
        """Test SMS delivery exception handling and fallback."""
        mock_sms.side_effect = Exception("SMS service error")
        mock_email.return_value = True

        result = OTPDeliveryService.send_otp(self.user_full_contacts, "123456", "login")

        self.assertTrue(result)
        mock_email.assert_called_once()

        mock_logger.error.assert_called()
        error_calls = mock_logger.error.call_args_list
        self.assertTrue(any("SMS service error" in str(call) for call in error_calls))

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_email_delivery_login_success(self, mock_logger, mock_email):
        """Test successful email delivery for login OTP."""
        mock_email.delay = Mock()

        result = OTPDeliveryService.send_otp(self.user_full_contacts, "123456", "login")

        self.assertTrue(result)
        mock_email.delay.assert_called_once()

        call_args = mock_email.delay.call_args[1]
        self.assertEqual("Your Login OTP Code", call_args["subject"])
        self.assertIn("123456", call_args["text_content"])
        self.assertEqual(self.user_full_contacts.email, call_args["to_email"])

        mock_logger.info.assert_called_with(
            f"OTP sent via email to {self.user_full_contacts.email}"
        )

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    def test_email_delivery_password_reset(self, mock_email):
        """Test email delivery for password reset OTP."""
        mock_email.delay = Mock()

        result = OTPDeliveryService.send_otp(
            self.user_full_contacts, "123456", "password_reset"
        )

        self.assertTrue(result)
        call_args = mock_email.delay.call_args[1]

        self.assertEqual("Password Reset OTP Code", call_args["subject"])
        self.assertIn("password reset", call_args["text_content"].lower())
        self.assertIn("123456", call_args["text_content"])

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    def test_email_delivery_verification(self, mock_email):
        """Test email delivery for verification OTP."""
        mock_email.delay = Mock()

        result = OTPDeliveryService.send_otp(
            self.user_full_contacts, "123456", "verification"
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

        result = OTPDeliveryService.send_otp(self.user_full_contacts, "123456", "login")

        self.assertFalse(result)
        mock_logger.error.assert_called()

        error_call = mock_logger.error.call_args[0][0]
        self.assertIn("Failed to send OTP email", error_call)
        self.assertIn("Email service unavailable", error_call)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_validate_user_sms_with_phone_success(self):
        """Test user validation for SMS delivery with valid phone."""
        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_full_contacts
        )

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_validate_user_sms_without_phone_failure(self):
        """Test user validation for SMS delivery without phone."""
        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_email_only
        )

        self.assertFalse(is_valid)
        self.assertIn("Phone number is required for SMS OTP delivery", error)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_validate_user_email_with_email_success(self):
        """Test user validation for email delivery with valid email."""
        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_full_contacts
        )

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_validate_user_email_without_email_failure(self):
        """Test user validation for email delivery without email."""

        user_no_email = User.objects.create_user(
            email="",
            password="password123",
            fullname="No Email User",
            phone_number="+5555555555",
            username="noemailtest",
        )

        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            user_no_email
        )

        self.assertFalse(is_valid)
        self.assertIn("Email address is required for email OTP delivery", error)

    @override_settings(OTP_DELIVERY_METHOD="invalid")
    def test_validate_user_invalid_delivery_method_defaults_to_email(self):
        """Test user validation with invalid delivery method defaults to email."""

        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_full_contacts
        )

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_delivery_target_display_sms_masking(self):
        """Test SMS delivery target display with phone number masking."""
        display = OTPDeliveryService.get_delivery_target_display(
            self.user_full_contacts
        )

        self.assertIn("SMS to", display)
        self.assertIn("+123", display)
        self.assertIn("7890", display)
        self.assertIn("*", display)

        self.assertNotIn("+1234567890", display)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_delivery_target_display_sms_short_phone(self):
        """Test SMS delivery target display with short phone number."""
        short_phone_user = User.objects.create_user(
            email="short@example.com",
            password="password123",
            phone_number="123",
            username="shortphone",
        )

        display = OTPDeliveryService.get_delivery_target_display(short_phone_user)

        self.assertIn("SMS to", display)
        self.assertIn("***", display)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_delivery_target_display_email_masking(self):
        """Test email delivery target display with email masking."""
        display = OTPDeliveryService.get_delivery_target_display(
            self.user_full_contacts
        )

        self.assertIn("email to", display)
        self.assertIn("fu", display)
        self.assertIn("*", display)
        self.assertIn(".com", display)

        self.assertNotIn("full@example.com", display)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_delivery_target_display_email_short_username(self):
        """Test email delivery target display with short username."""
        short_email_user = User.objects.create_user(
            email="ab@example.com",
            password="password123",
            username="shortmail",
        )

        display = OTPDeliveryService.get_delivery_target_display(short_email_user)

        self.assertIn("email to", display)
        self.assertIn("**@", display)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_delivery_target_display_sms_fallback_to_email(self):
        """Test delivery target display falls back to email when SMS user has no phone."""
        display = OTPDeliveryService.get_delivery_target_display(self.user_email_only)

        self.assertIn("email to", display)

    def test_otp_message_content_variations(self):
        """Test different OTP message content for various types."""
        otp_types = {
            "login": "login otp code",
            "password_reset": "password reset otp code",
            "verification": "verification otp code",
        }

        for otp_type, expected_content in otp_types.items():
            with self.subTest(otp_type=otp_type):
                with override_settings(OTP_DELIVERY_METHOD="sms"):
                    with patch(
                        "apps.accounts.auth.services.otp_delivery_service.send_sms_neons"
                    ) as mock_sms:
                        mock_sms.return_value = True

                        OTPDeliveryService.send_otp(
                            self.user_full_contacts, "123456", otp_type
                        )

                        call_args = mock_sms.call_args[0]
                        message = call_args[0].lower()

                        self.assertIn(expected_content, message)
                        self.assertIn("123456", message)
                        self.assertIn("10 minutes", message)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_end_to_end_sms_delivery_flow(self):
        """Test complete SMS delivery flow with all components."""
        with (
            patch(
                "apps.accounts.auth.services.otp_delivery_service.send_sms_neons"
            ) as mock_sms,
            patch(
                "apps.accounts.auth.services.otp_delivery_service.logger"
            ) as mock_logger,
        ):

            mock_sms.return_value = True

            result = OTPDeliveryService.send_otp(
                self.user_full_contacts, "987654", "password_reset"
            )

            self.assertTrue(result)

            call_args = mock_sms.call_args[0]
            message, phone_numbers = call_args

            self.assertIn("987654", message)
            self.assertIn("password reset", message.lower())
            self.assertEqual(["+1234567890"], phone_numbers)

            mock_logger.info.assert_called()

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_end_to_end_email_delivery_flow(self):
        """Test complete email delivery flow with all components."""
        with (
            patch(
                "apps.accounts.auth.services.otp_delivery_service.send_activation_email"
            ) as mock_email,
            patch(
                "apps.accounts.auth.services.otp_delivery_service.logger"
            ) as mock_logger,
        ):

            mock_email.delay = Mock()

            result = OTPDeliveryService.send_otp(
                self.user_full_contacts, "456789", "verification"
            )

            self.assertTrue(result)

            call_args = mock_email.delay.call_args[1]

            self.assertIn("456789", call_args["text_content"])
            self.assertIn("verification", call_args["subject"].lower())
            self.assertEqual(self.user_full_contacts.email, call_args["to_email"])

            mock_logger.info.assert_called()

    def test_delivery_method_configuration_override(self):
        """Test that delivery method can be overridden dynamically."""

        with override_settings(OTP_DELIVERY_METHOD="email"):
            self.assertEqual(OTPDeliveryService.get_delivery_method(), "email")

        with override_settings(OTP_DELIVERY_METHOD="sms"):
            self.assertEqual(OTPDeliveryService.get_delivery_method(), "sms")

        with override_settings(OTP_DELIVERY_METHOD=""):
            self.assertEqual(OTPDeliveryService.get_delivery_method(), "email")

    def test_service_resilience_to_invalid_inputs(self):
        """Test service handles invalid inputs gracefully."""

        with self.assertRaises(AttributeError):
            OTPDeliveryService.send_otp(None, "123456", "login")

        result = OTPDeliveryService.send_otp(self.user_full_contacts, "", "login")

        with override_settings(OTP_DELIVERY_METHOD="email"):
            with patch(
                "apps.accounts.auth.services.otp_delivery_service.send_activation_email"
            ) as mock_email:
                mock_email.delay = Mock()

                result = OTPDeliveryService.send_otp(
                    self.user_full_contacts, "123456", "invalid_type"
                )

                self.assertTrue(result)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("apps.accounts.auth.services.otp_delivery_service.logger")
    def test_comprehensive_logging_behavior(self, mock_logger):
        """Test comprehensive logging behavior across different scenarios."""

        with patch(
            "apps.accounts.auth.services.otp_delivery_service.send_sms"
        ) as mock_sms:
            mock_sms.return_value = True
            OTPDeliveryService.send_otp(self.user_full_contacts, "123456", "login")
            mock_logger.info.assert_called()

        mock_logger.reset_mock()

        OTPDeliveryService.send_otp(self.user_email_only, "123456", "login")
        mock_logger.error.assert_called()

    def test_multiple_concurrent_delivery_requests(self):
        """Test handling of multiple concurrent delivery requests."""
        import threading

        results = []

        def send_otp_thread(user, code):
            with override_settings(OTP_DELIVERY_METHOD="email"):
                with patch(
                    "apps.accounts.auth.services.otp_delivery_service.send_activation_email"
                ) as mock_email:
                    mock_email.delay = Mock()
                    result = OTPDeliveryService.send_otp(user, code, "login")
                    results.append(result)

        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=send_otp_thread, args=(self.user_full_contacts, f"12345{i}")
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(results), 5)
        self.assertTrue(all(results))
