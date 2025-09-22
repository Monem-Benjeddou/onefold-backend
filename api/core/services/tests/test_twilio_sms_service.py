"""
Comprehensive test suite for Twilio SMS service.
Tests SMS functionality without affecting SendGrid email services.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import SimpleTestCase, override_settings
from django.core.cache import cache

from core.services.twilio_sms_service import (
    TwilioSMSService,
    CommunicationResult,
    ServiceStatus,
)


class TestTwilioSMSService(SimpleTestCase):
    """Test cases for Twilio SMS service (SMS only)."""

    def setUp(self):
        cache.clear()
        self.mock_twilio_config = {
            "TWILIO_ACCOUNT_SID": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "TWILIO_AUTH_TOKEN": "test-auth-token",
            "TWILIO_SMS_FROM_NUMBER": "+15551234567",
            "TWILIO_VERIFY_SERVICE_SID": "VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        }

    @override_settings(
        **{
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_SMS_FROM_NUMBER": "+15551234567",
        }
    )
    @patch("core.services.twilio_sms_service.Client")
    def test_service_initialization(self, mock_twilio):
        """Test that Twilio SMS service initializes correctly."""
        service = TwilioSMSService()

        self.assertTrue(service.is_sms_configured())
        mock_twilio.assert_called_with("test_sid", "test_token")

    @override_settings(
        **{
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_SMS_FROM_NUMBER": "+15551234567",
        }
    )
    @patch("core.services.twilio_sms_service.Client")
    def test_send_sms_success(self, mock_twilio_client):
        """Test successful SMS sending via Twilio."""

        mock_message = Mock()
        mock_message.sid = "SMaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_twilio_client.return_value = mock_client

        service = TwilioSMSService()
        result = service.send_sms(
            phone_number="+15559876543", message="Test SMS message"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.message_id, "SMaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        self.assertEqual(result.service_used, "twilio_sms")

    @override_settings(
        **{
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_SMS_FROM_NUMBER": "+15551234567",
        }
    )
    @patch("core.services.twilio_sms_service.Client")
    def test_sms_failure_handling(self, mock_twilio_client):
        """Test SMS failure handling (no retry - single attempt only)."""
        from twilio.base.exceptions import TwilioException

        mock_client = Mock()
        mock_client.messages.create.side_effect = TwilioException("Temporary failure")
        mock_twilio_client.return_value = mock_client

        service = TwilioSMSService()
        result = service.send_sms(
            phone_number="+15559876543", message="Test failure message"
        )

        self.assertFalse(result.success)
        self.assertEqual(result.retry_count, 0)  
        self.assertEqual(result.error, "Temporary failure")
        self.assertIsNone(result.message_id)

    def test_phone_number_formatting(self):
        """Test phone number formatting for E.164 format."""
        service = TwilioSMSService()

        test_cases = [
            ("5551234567", "+5551234567"),
            ("+15551234567", "+15551234567"),
            ("0015551234567", "+15551234567"),
            ("+966501234567", "+966501234567"),
            ("00966501234567", "+966501234567"),
            ("966501234567", "+966501234567"),
            ("+21626716816", "+21626716816"),
            ("", None),
            ("abc123", None),
        ]

        for input_number, expected in test_cases:
            result = service._format_phone_number(input_number)
            self.assertEqual(result, expected, f"Failed for input: {input_number}")

    @override_settings(
        **{
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_VERIFY_SERVICE_SID": "test_verify_sid",
        }
    )
    @patch("core.services.twilio_sms_service.Client")
    def test_send_verification_code(self, mock_twilio_client):
        """Test sending verification code via Twilio Verify."""
        mock_verification = Mock()
        mock_verification.sid = "VEaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

        mock_verify = Mock()
        mock_verify.verify.v2.services.return_value.verifications.create.return_value = (
            mock_verification
        )
        mock_twilio_client.return_value = mock_verify

        service = TwilioSMSService()
        result = service.send_verification_code("+15559876543", "sms")

        self.assertTrue(result.success)
        self.assertEqual(result.message_id, "VEaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        self.assertEqual(result.service_used, "twilio_verify")

    @override_settings(
        **{
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_VERIFY_SERVICE_SID": "test_verify_sid",
        }
    )
    @patch("core.services.twilio_sms_service.Client")
    def test_verify_code_success(self, mock_twilio_client):
        """Test successful code verification."""
        mock_check = Mock()
        mock_check.sid = "VCaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        mock_check.status = "approved"

        mock_verify = Mock()
        mock_verify.verify.v2.services.return_value.verification_checks.create.return_value = (
            mock_check
        )
        mock_twilio_client.return_value = mock_verify

        service = TwilioSMSService()
        result = service.verify_code("+15559876543", "123456")

        self.assertTrue(result.success)
        self.assertEqual(result.message_id, "VCaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

    @override_settings(
        **{
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_VERIFY_SERVICE_SID": "test_verify_sid",
        }
    )
    @patch("core.services.twilio_sms_service.Client")
    def test_verify_code_failure(self, mock_twilio_client):
        """Test failed code verification."""
        mock_check = Mock()
        mock_check.sid = "VCaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        mock_check.status = "pending"

        mock_verify = Mock()
        mock_verify.verify.v2.services.return_value.verification_checks.create.return_value = (
            mock_check
        )
        mock_twilio_client.return_value = mock_verify

        service = TwilioSMSService()
        result = service.verify_code("+15559876543", "999999")

        self.assertFalse(result.success)
        self.assertIn("pending", result.error)

    @override_settings(
        TWILIO_ACCOUNT_SID=None,
        TWILIO_AUTH_TOKEN=None,
        TWILIO_SMS_FROM_NUMBER=None,
    )
    def test_service_not_configured(self):
        """Test service behavior when not configured."""
        service = TwilioSMSService()

        result = service.send_sms("+15559876543", "Test message")

        self.assertFalse(result.success)
        self.assertEqual(result.error, "SMS service not configured")
        self.assertEqual(result.service_used, "twilio_sms")

    @override_settings(
        **{
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_SMS_FROM_NUMBER": "+1234567890",  
        }
    )
    @patch("core.services.twilio_sms_service.Client")
    def test_placeholder_from_number_rejected(self, mock_twilio_client):
        """Test that placeholder from numbers are rejected."""
        service = TwilioSMSService()

        
        self.assertFalse(service.is_sms_configured())

        result = service.send_sms("+15559876543", "Test message")

        self.assertFalse(result.success)
        self.assertEqual(result.error, "SMS service not configured")
        self.assertEqual(result.service_used, "twilio_sms")

    @override_settings(
        **{
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_SMS_FROM_NUMBER": "+15005550006",  
        }
    )
    @patch("core.services.twilio_sms_service.Client")
    def test_twilio_magic_number_rejected(self, mock_twilio_client):
        """Test that Twilio's magic test number is rejected."""
        service = TwilioSMSService()

        
        self.assertFalse(service.is_sms_configured())

        result = service.send_sms("+15559876543", "Test message")

        self.assertFalse(result.success)
        self.assertEqual(result.error, "SMS service not configured")
        self.assertEqual(result.service_used, "twilio_sms")

    @override_settings(
        **{
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_SMS_FROM_NUMBER": "+15551234567",
        }
    )
    @patch("core.services.twilio_sms_service.Client")
    def test_health_check(self, mock_twilio_client):
        """Test health check functionality."""
        mock_account = Mock()
        mock_account.status = "active"

        mock_client = Mock()
        mock_client.api.accounts.return_value.fetch.return_value = mock_account
        mock_twilio_client.return_value = mock_client

        service = TwilioSMSService()
        health = service.health_check()

        self.assertEqual(health["service"], "twilio_sms")
        self.assertIn("services", health)
        self.assertIn("twilio_sms", health["services"])
        self.assertEqual(
            health["services"]["twilio_sms"]["status"], ServiceStatus.HEALTHY.value
        )

    @override_settings(
        **{
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_SMS_FROM_NUMBER": "+1234567890",  
        }
    )
    @patch("core.services.twilio_sms_service.Client")
    def test_health_check_with_placeholder_number(self, mock_twilio_client):
        """Test health check when using placeholder number."""
        service = TwilioSMSService()
        health = service.health_check()

        self.assertEqual(health["service"], "twilio_sms")
        self.assertEqual(health["overall_status"], ServiceStatus.UNHEALTHY.value)
        self.assertIn("services", health)
        self.assertIn("twilio_sms", health["services"])
        self.assertEqual(
            health["services"]["twilio_sms"]["status"], ServiceStatus.UNHEALTHY.value
        )
        self.assertIn(
            "placeholder/test number", health["services"]["twilio_sms"]["message"]
        )
