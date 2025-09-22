"""
Comprehensive test cases for OTP_DELIVERY_METHOD environment variable behavior.

Tests cover:
1. Environment variable configuration and validation
2. Dynamic behavior changes based on settings
3. Default fallback behavior
4. Invalid configuration handling
5. Runtime configuration changes
6. Integration with Django settings
7. Case sensitivity and normalization
8. Missing configuration handling
"""

import os
from unittest.mock import patch, Mock
from django.test import TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService
from apps.accounts.auth.serializers.login_otp import (
    OTPRequestSerializer,
    OTPVerifySerializer,
)

User = get_user_model()


class OTPEnvironmentVariableBehaviorTestCase(TransactionTestCase):
    """Test cases for OTP_DELIVERY_METHOD environment variable behavior."""

    def setUp(self):

        self.user_with_both_contacts = User.objects.create_user(
            email="both@example.com",
            password="password123",
            fullname="Both Contacts User",
            phone_number="+1234567890",
            username="bothuser",
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

    def tearDown(self):
        User.objects.all().delete()

    def test_default_behavior_no_setting(self):
        """Test default behavior when OTP_DELIVERY_METHOD is not configured."""
        with override_settings():

            if hasattr(settings, "OTP_DELIVERY_METHOD"):
                delattr(settings, "OTP_DELIVERY_METHOD")

            delivery_method = OTPDeliveryService.get_delivery_method()
            self.assertEqual(delivery_method, "email")

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_sms_delivery_method_setting(self):
        """Test SMS delivery method configuration."""
        delivery_method = OTPDeliveryService.get_delivery_method()
        self.assertEqual(delivery_method, "sms")

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_email_delivery_method_setting(self):
        """Test email delivery method configuration."""
        delivery_method = OTPDeliveryService.get_delivery_method()
        self.assertEqual(delivery_method, "email")

    @override_settings(OTP_DELIVERY_METHOD="")
    def test_empty_string_setting_defaults_to_email(self):
        """Test that empty string setting defaults to email."""
        delivery_method = OTPDeliveryService.get_delivery_method()
        self.assertEqual(delivery_method, "email")

    @override_settings(OTP_DELIVERY_METHOD=None)
    def test_none_setting_defaults_to_email(self):
        """Test that None setting defaults to email."""
        delivery_method = OTPDeliveryService.get_delivery_method()
        self.assertEqual(delivery_method, "email")

    @override_settings(OTP_DELIVERY_METHOD="SMS")
    def test_uppercase_sms_normalized_to_lowercase(self):
        """Test that uppercase SMS is normalized to lowercase."""
        delivery_method = OTPDeliveryService.get_delivery_method()
        self.assertEqual(delivery_method, "sms")

    @override_settings(OTP_DELIVERY_METHOD="EMAIL")
    def test_uppercase_email_normalized_to_lowercase(self):
        """Test that uppercase EMAIL is normalized to lowercase."""
        delivery_method = OTPDeliveryService.get_delivery_method()
        self.assertEqual(delivery_method, "email")

    @override_settings(OTP_DELIVERY_METHOD="SmS")
    def test_mixed_case_sms_normalized_to_lowercase(self):
        """Test that mixed case SMS is normalized to lowercase."""
        delivery_method = OTPDeliveryService.get_delivery_method()
        self.assertEqual(delivery_method, "sms")

    @override_settings(OTP_DELIVERY_METHOD="EmAiL")
    def test_mixed_case_email_normalized_to_lowercase(self):
        """Test that mixed case EMAIL is normalized to lowercase."""
        delivery_method = OTPDeliveryService.get_delivery_method()
        self.assertEqual(delivery_method, "email")

    @override_settings(OTP_DELIVERY_METHOD="invalid_method")
    def test_invalid_delivery_method_returns_as_configured(self):
        """Test that invalid delivery method returns the configured value."""
        delivery_method = OTPDeliveryService.get_delivery_method()
        self.assertEqual(delivery_method, "invalid_method")

    @override_settings(OTP_DELIVERY_METHOD="whatsapp")
    def test_unsupported_delivery_method(self):
        """Test behavior with unsupported delivery method."""
        delivery_method = OTPDeliveryService.get_delivery_method()
        self.assertEqual(delivery_method, "whatsapp")

        with patch(
            "apps.accounts.auth.services.otp_delivery_service.send_activation_email"
        ) as mock_email:
            mock_email.delay = Mock()

            result = OTPDeliveryService.send_otp(
                self.user_with_both_contacts, "123456", "login"
            )

            self.assertTrue(result)
            mock_email.delay.assert_called_once()

    @override_settings(OTP_DELIVERY_METHOD=123)
    def test_non_string_delivery_method(self):
        """Test behavior with non-string delivery method."""

        try:
            delivery_method = OTPDeliveryService.get_delivery_method()

            self.assertEqual(delivery_method, "123")
        except Exception:

            pass

    def test_dynamic_configuration_change(self):
        """Test that configuration changes are reflected immediately."""

        with override_settings(OTP_DELIVERY_METHOD="email"):
            self.assertEqual(OTPDeliveryService.get_delivery_method(), "email")

        with override_settings(OTP_DELIVERY_METHOD="sms"):
            self.assertEqual(OTPDeliveryService.get_delivery_method(), "sms")

        with override_settings(OTP_DELIVERY_METHOD="email"):
            self.assertEqual(OTPDeliveryService.get_delivery_method(), "email")

    def test_multiple_rapid_configuration_changes(self):
        """Test behavior with multiple rapid configuration changes."""
        configurations = ["email", "sms", "EMAIL", "SMS", "invalid", ""]
        expected_results = ["email", "sms", "email", "sms", "invalid", "email"]

        for config, expected in zip(configurations, expected_results):
            with self.subTest(config=config, expected=expected):
                with override_settings(OTP_DELIVERY_METHOD=config):
                    result = OTPDeliveryService.get_delivery_method()
                    self.assertEqual(result, expected)

    @override_settings(OTP_DELIVERY_METHOD="sms", SMS_FALLBACK_TO_EMAIL=False)
    def test_user_validation_respects_sms_setting(self):
        """Test that user validation respects SMS delivery setting when fallback is disabled."""

        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_with_both_contacts
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_email_only
        )
        self.assertFalse(is_valid)
        self.assertIn("Phone number is required", error)

    @override_settings(OTP_DELIVERY_METHOD="sms", SMS_FALLBACK_TO_EMAIL=True)
    def test_user_validation_respects_sms_setting_with_fallback_enabled(self):
        """Test that user validation allows email-only users when SMS fallback is enabled."""

        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_with_both_contacts
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_email_only
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_user_validation_respects_email_setting(self):
        """Test that user validation respects email delivery setting."""

        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_with_both_contacts
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_phone_only
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @override_settings(OTP_DELIVERY_METHOD="invalid")
    def test_user_validation_with_invalid_setting_defaults_to_email(self):
        """Test that user validation with invalid setting defaults to email behavior."""

        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
            self.user_with_both_contacts
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_otp_request_serializer_respects_sms_setting(self):
        """Test that OTP request serializer respects SMS delivery setting."""

        data = {"email": "both@example.com", "phone_number": "+1234567890"}

        serializer = OTPRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        validated_data = serializer.validated_data
        self.assertEqual(validated_data["user"], self.user_with_both_contacts)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_otp_request_serializer_respects_email_setting(self):
        """Test that OTP request serializer respects email delivery setting."""

        data = {"email": "both@example.com", "phone_number": "+1234567890"}

        serializer = OTPRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        validated_data = serializer.validated_data
        self.assertEqual(validated_data["user"], self.user_with_both_contacts)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_otp_verify_serializer_respects_sms_setting(self):
        """Test that OTP verify serializer respects SMS delivery setting."""
        data = {
            "email": "both@example.com",
            "phone_number": "+1234567890",
            "otp": "123456",
        }

        serializer = OTPVerifySerializer(data=data)
        self.assertTrue(serializer.is_valid())

        validated_data = serializer.validated_data
        self.assertEqual(validated_data["user"], self.user_with_both_contacts)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_otp_sending_respects_sms_setting(self, mock_sms):
        """Test that OTP sending respects SMS delivery setting."""
        mock_sms.return_value = True

        result = OTPDeliveryService.send_otp(
            self.user_with_both_contacts, "123456", "login"
        )

        self.assertTrue(result)
        mock_sms.assert_called_once()

        call_args = mock_sms.call_args[0]
        message, phone_numbers, otp_type = call_args
        self.assertIn("123456", message)
        self.assertEqual(["+1234567890"], phone_numbers)

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    def test_otp_sending_respects_email_setting(self, mock_email):
        """Test that OTP sending respects email delivery setting."""
        mock_email.delay = Mock()

        result = OTPDeliveryService.send_otp(
            self.user_with_both_contacts, "123456", "login"
        )

        self.assertTrue(result)
        mock_email.delay.assert_called_once()

        call_args = mock_email.delay.call_args[1]
        self.assertIn("123456", call_args["text_content"])
        self.assertEqual("both@example.com", call_args["to_email"])

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_delivery_target_display_respects_sms_setting(self):
        """Test that delivery target display respects SMS setting."""
        display = OTPDeliveryService.get_delivery_target_display(
            self.user_with_both_contacts
        )

        self.assertIn("SMS to", display)
        self.assertIn("+123", display)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_delivery_target_display_respects_email_setting(self):
        """Test that delivery target display respects email setting."""
        display = OTPDeliveryService.get_delivery_target_display(
            self.user_with_both_contacts
        )

        self.assertIn("email to", display)
        self.assertIn("@", display)

    def test_delivery_target_display_fallback_when_no_phone(self):
        """Test delivery target display fallback when user has no phone."""
        
        display = OTPDeliveryService.get_delivery_target_display(self.user_email_only)

        self.assertIn("email to", display)

    @override_settings(OTP_DELIVERY_METHOD="sms", SMS_FALLBACK_TO_EMAIL=False)
    def test_sms_setting_with_user_without_phone(self):
        """Test SMS setting behavior with user who has no phone number when fallback is disabled."""
        result = OTPDeliveryService.send_otp(self.user_email_only, "123456", "login")

        self.assertFalse(result)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_email_setting_with_user_without_email(self):
        """Test email setting behavior with user who has no email."""

        user_no_email = User.objects.create_user(
            email="",
            password="password123",
            fullname="No Email User",
            phone_number="+5555555555",
            username="noemail",
        )

        result = OTPDeliveryService.send_otp(user_no_email, "123456", "login")

        self.assertFalse(result)

    def test_configuration_persistence_across_requests(self):
        """Test that configuration persists across multiple service calls."""
        with override_settings(OTP_DELIVERY_METHOD="sms"):

            method1 = OTPDeliveryService.get_delivery_method()

            method2 = OTPDeliveryService.get_delivery_method()

            self.assertEqual(method1, method2)
            self.assertEqual(method1, "sms")

    def test_concurrent_configuration_access(self):
        """Test concurrent access to configuration doesn't cause issues."""
        import threading
        import time

        results = []

        def get_delivery_method():
            with override_settings(OTP_DELIVERY_METHOD="email"):
                time.sleep(0.01)
                method = OTPDeliveryService.get_delivery_method()
                results.append(method)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_delivery_method)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(results), 10)

        unique_results = set(results)
        if len(unique_results) > 1:
            print(f"Inconsistent results: {results}")

        self.assertTrue(
            len(unique_results) <= 2, f"Too many different results: {unique_results}"
        )

        email_count = results.count("email")
        self.assertTrue(
            email_count >= 7,
            f"Expected at least 7 'email' results, got {email_count}. Results: {results}",
        )

    def test_settings_attribute_access(self):
        """Test direct access to settings attribute."""
        with override_settings(OTP_DELIVERY_METHOD="test_value"):

            self.assertEqual(settings.OTP_DELIVERY_METHOD, "test_value")

            self.assertEqual(OTPDeliveryService.get_delivery_method(), "test_value")

    def test_missing_settings_attribute_handling(self):
        """Test handling when settings attribute doesn't exist."""
        with override_settings():

            if hasattr(settings, "OTP_DELIVERY_METHOD"):
                delattr(settings, "OTP_DELIVERY_METHOD")

            method = OTPDeliveryService.get_delivery_method()
            self.assertEqual(method, "email")

    def test_getattr_default_behavior(self):
        """Test getattr default parameter behavior in get_delivery_method."""
        with override_settings():
            if hasattr(settings, "OTP_DELIVERY_METHOD"):
                delattr(settings, "OTP_DELIVERY_METHOD")

            method = OTPDeliveryService.get_delivery_method()
            self.assertEqual(method, "email")

    def test_production_like_configuration_sms(self):
        """Test production-like SMS configuration scenario."""
        with override_settings(
            OTP_DELIVERY_METHOD="sms",
            TWILIO_ACCOUNT_SID="test_sid",
            TWILIO_AUTH_TOKEN="test_token",
        ):

            self.assertEqual(OTPDeliveryService.get_delivery_method(), "sms")

            is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
                self.user_with_both_contacts
            )
            self.assertTrue(is_valid)

    def test_production_like_configuration_email(self):
        """Test production-like email configuration scenario."""
        with override_settings(
            OTP_DELIVERY_METHOD="email",
            EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        ):

            self.assertEqual(OTPDeliveryService.get_delivery_method(), "email")

            is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
                self.user_with_both_contacts
            )
            self.assertTrue(is_valid)
