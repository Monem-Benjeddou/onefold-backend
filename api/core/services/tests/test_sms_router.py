"""
Test suite for SMS routing service.
Tests country-based routing between Neons (Saudi) and Twilio (International).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.core.cache import cache

from core.services.sms_router import SMSRouter, SMSProvider
from core.services.twilio_sms_service import CommunicationResult


class TestSMSRouter(TestCase):
    """Test cases for SMS routing service."""

    def setUp(self):
        cache.clear()

    def test_provider_detection(self):
        """Test provider detection based on country codes."""
        router = SMSRouter()

        
        provider = router._detect_provider("+966501234567")
        self.assertEqual(provider, SMSProvider.NEONS)

        provider = router._detect_provider("966501234567")
        self.assertEqual(provider, SMSProvider.NEONS)

        provider = router._detect_provider("00966501234567")
        self.assertEqual(provider, SMSProvider.NEONS)

        
        provider = router._detect_provider("+33123456789")
        self.assertEqual(provider, SMSProvider.TWILIO)

        provider = router._detect_provider("+1234567890")
        self.assertEqual(provider, SMSProvider.TWILIO)

        provider = router._detect_provider("+216123456789")
        self.assertEqual(provider, SMSProvider.TWILIO)

        provider = router._detect_provider("+44123456789")
        self.assertEqual(provider, SMSProvider.TWILIO)

    @patch("core.services.sms_router.NeonsSMSService")
    def test_send_sms_neons_routing(self, mock_neons_class):
        """Test SMS sending via Neons service for Saudi numbers."""
        mock_neons = Mock()
        mock_neons.send_sms.return_value = {
            "success": True,
            "response": {"id": "neons_message_id"},
        }
        mock_neons.is_configured.return_value = True
        mock_neons_class.return_value = mock_neons

        router = SMSRouter()
        result = router.send_sms("+966501234567", "Test message")

        self.assertTrue(result.success)
        self.assertEqual(result.service_used, "neons_sms")
        mock_neons.send_sms.assert_called_once_with("+966501234567", "Test message")

    @patch("core.services.sms_router.twilio_sms_service")
    def test_send_sms_twilio_routing(self, mock_twilio):
        """Test SMS sending via Twilio for international numbers."""
        mock_twilio.send_sms.return_value = CommunicationResult(
            success=True, message_id="twilio_message_id", service_used="twilio_sms"
        )
        mock_twilio.is_sms_configured.return_value = True

        router = SMSRouter()
        result = router.send_sms("+1234567890", "Test message")

        self.assertTrue(result.success)
        self.assertEqual(result.service_used, "twilio_sms")
        mock_twilio.send_sms.assert_called_once()

    @patch("core.services.sms_router.twilio_sms_service")
    @patch("core.services.sms_router.NeonsSMSService")
    def test_force_provider_override(self, mock_neons_class, mock_twilio):
        """Test forcing specific provider regardless of routing."""
        mock_twilio.send_sms.return_value = CommunicationResult(
            success=True, message_id="forced_twilio_id", service_used="twilio_sms"
        )
        mock_twilio.is_sms_configured.return_value = True

        mock_neons = Mock()
        mock_neons.is_configured.return_value = True
        mock_neons_class.return_value = mock_neons

        router = SMSRouter()

        result = router.send_sms(
            "+966501234567", "Test message", force_provider=SMSProvider.TWILIO
        )

        self.assertTrue(result.success)
        self.assertEqual(result.service_used, "twilio_sms")
        mock_twilio.send_sms.assert_called_once()

    @patch("core.services.sms_router.NeonsSMSService")
    def test_otp_message_templates(self, mock_neons_class):
        """Test OTP message template generation."""
        mock_neons = Mock()
        mock_neons.send_sms.return_value = {"success": True}
        mock_neons.is_configured.return_value = True
        mock_neons_class.return_value = mock_neons

        router = SMSRouter()
        result = router.send_otp_sms("+966501234567", "123456", "login")

        call_args = mock_neons.send_sms.call_args
        self.assertIn("123456", call_args[0][1])
        self.assertIn("Kolct", call_args[0][1])
        self.assertIn("10 minutes", call_args[0][1])


    def test_phone_number_normalization(self):
        """Test phone number normalization for routing."""
        router = SMSRouter()

        test_cases = [
            ("+966501234567", "966501234567"),
            ("00966501234567", "966501234567"),
            ("966501234567", "966501234567"),
            ("+1234567890", "1234567890"),
            ("001234567890", "1234567890"),
        ]

        for input_number, expected in test_cases:
            result = router._normalize_phone_number(input_number)
            self.assertEqual(result, expected, f"Failed for {input_number}")


    @patch("core.services.sms_router.twilio_sms_service")
    @patch("core.services.sms_router.NeonsSMSService")
    def test_get_routing_status(self, mock_neons_class, mock_twilio):
        """Test simple routing status report."""
        mock_neons = Mock()
        mock_neons.is_configured.return_value = True
        mock_neons_class.return_value = mock_neons

        mock_twilio.is_sms_configured.return_value = True
        mock_twilio.health_check.return_value = {
            "overall_status": "healthy",
            "services": {"twilio_sms": {"status": "healthy"}},
        }

        router = SMSRouter()
        status = router.get_routing_status()

        self.assertIn("routing_rules", status)
        self.assertIn("services", status)

        self.assertIn("saudi_arabia", status["routing_rules"])
        self.assertIn("international", status["routing_rules"])

        self.assertIn("neons", status["services"])
        self.assertIn("twilio", status["services"])

    def test_invalid_input_handling(self):
        """Test handling of invalid inputs."""
        router = SMSRouter()

        result = router.send_sms("", "Message")
        self.assertFalse(result.success)
        self.assertIn("required", result.error)

        result = router.send_sms("+1234567890", "")
        self.assertFalse(result.success)
        self.assertIn("required", result.error)

        result = router.send_sms("", "")
        self.assertFalse(result.success)
