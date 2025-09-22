"""
Test suite for unified communication service.
Verifies that SendGrid email continues to work unchanged while SMS routing is added.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from django.test import TestCase, override_settings
from django.core.cache import cache

from core.services.communication_service import (
    CommunicationService,
    CommunicationResult,
)


class TestCommunicationService(TestCase):
    """Test cases for unified communication service."""

    def setUp(self):
        cache.clear()

    @patch("core.services.communication_service.send_sendgrid_email")
    def test_send_email_uses_sendgrid(self, mock_sendgrid):
        """Test that email sending continues to use SendGrid (UNCHANGED)."""
        mock_sendgrid.return_value = 202

        service = CommunicationService()
        result = service.send_email(
            to_emails="test@example.com",
            subject="Test Subject",
            text_content="Test content",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.service_used, "sendgrid")
        mock_sendgrid.assert_called_once_with(
            to_emails="test@example.com",
            subject="Test Subject",
            text_content="Test content",
            html_content=None,
            from_email=None,
            reply_to=None,
        )

    @patch("core.services.communication_service.sms_router")
    def test_send_sms_uses_router(self, mock_router):
        """Test SMS sending uses the SMS router."""
        mock_router.send_sms.return_value = CommunicationResult(
            success=True, message_id="comm_sms_id", service_used="neons_sms"
        )

        service = CommunicationService()
        result = service.send_sms("+966501234567", "Test SMS")

        self.assertTrue(result.success)
        mock_router.send_sms.assert_called_once()

    @patch("core.services.communication_service.send_sendgrid_email")
    @patch("core.services.communication_service.sms_router")
    def test_dual_otp_sending(self, mock_router, mock_sendgrid):
        """Test sending OTP via both email (SendGrid) and SMS (Router)."""
        mock_sendgrid.return_value = 202
        mock_router.send_otp_sms.return_value = CommunicationResult(
            success=True, message_id="sms_otp_id", service_used="neons_sms"
        )

        service = CommunicationService()
        results = service.send_dual_otp(
            email="test@example.com",
            phone_number="+966501234567",
            otp_code="123456",
            otp_type="login",
        )

        self.assertTrue(results["email"].success)
        self.assertTrue(results["sms"].success)
        self.assertEqual(len(results), 2)

        mock_sendgrid.assert_called_once()

        mock_router.send_otp_sms.assert_called_once()

    @patch("core.services.communication_service.send_sendgrid_email")
    def test_send_otp_email_templates(self, mock_sendgrid):
        """Test OTP email template formatting (via SendGrid)."""
        mock_sendgrid.return_value = 202

        service = CommunicationService()

        result = service.send_otp_email("test@example.com", "123456", "login")

        call_args = mock_sendgrid.call_args
        self.assertIn("123456", call_args[1]["text_content"])
        self.assertIn("Login Code", call_args[1]["subject"])

        result = service.send_otp_email("test@example.com", "654321", "registration")

        call_args = mock_sendgrid.call_args
        self.assertIn("654321", call_args[1]["text_content"])
        self.assertIn("Welcome", call_args[1]["subject"])

    @patch("core.services.communication_service.sms_router")
    def test_send_otp_sms_templates(self, mock_router):
        """Test OTP SMS template formatting."""
        mock_router.send_otp_sms.return_value = CommunicationResult(success=True)

        service = CommunicationService()
        result = service.send_otp_sms("+966501234567", "123456", "login")

        mock_router.send_otp_sms.assert_called_once_with(
            phone_number="+966501234567", otp_code="123456", otp_type="login"
        )

    def test_performance_tracking(self):
        """Test performance metrics tracking."""
        with patch(
            "core.services.communication_service.send_sendgrid_email"
        ) as mock_sendgrid:
            mock_sendgrid.return_value = 202

            service = CommunicationService()

            for i in range(3):
                service.send_email(f"test{i}@example.com", "Subject", "Content")

            stats = service._get_performance_statistics()
            self.assertEqual(stats["email"]["total_requests"], 3)
            self.assertEqual(stats["email"]["success_count"], 3)
            self.assertEqual(stats["email"]["success_rate_percent"], 100.0)

    @patch("core.services.communication_service.send_sendgrid_email")
    def test_email_error_handling(self, mock_sendgrid):
        """Test email error handling (SendGrid errors)."""
        mock_sendgrid.side_effect = Exception("SendGrid API error")

        service = CommunicationService()
        result = service.send_email("test@example.com", "Subject", "Content")

        self.assertFalse(result.success)
        self.assertEqual(result.service_used, "sendgrid")
        self.assertIn("SendGrid API error", result.error)

    @patch("core.services.communication_service.sms_router")
    def test_sms_provider_forcing(self, mock_router):
        """Test forcing specific SMS provider."""
        mock_router.send_sms.return_value = CommunicationResult(success=True)

        service = CommunicationService()

        result = service.send_sms("+966501234567", "Test", force_provider="twilio")

        call_args = mock_router.send_sms.call_args
        self.assertEqual(call_args[1]["force_provider"].value, "twilio")

    @patch("core.services.communication_service.twilio_sms_service")
    @patch("core.services.communication_service.sms_router")
    def test_service_health_check(self, mock_router, mock_twilio):
        """Test comprehensive health check for all services."""

        mock_twilio.health_check.return_value = {
            "overall_status": "healthy",
            "services": {"twilio_sms": {"status": "healthy"}},
        }

        mock_router.get_routing_status.return_value = {
            "routing_rules": {},
            "services": {
                "neons": {"status": "healthy"},
                "twilio": {"status": "healthy"},
            },
            "statistics": {},
        }

        with override_settings(SENDGRID_API_KEY="test_key"):
            service = CommunicationService()
            health = service.get_service_health()

            self.assertIn("overall_status", health)
            self.assertIn("services", health)
            self.assertIn("sendgrid_email", health["services"])
            self.assertIn("twilio_sms", health["services"])
            self.assertIn("sms_routing", health["services"])
            self.assertIn("performance", health)

    def test_template_application(self):
        """Test template application for emails and SMS."""
        service = CommunicationService()

        text, html, subject = service._apply_email_template(
            "otp_login",
            "Your code is: {}",
            "<p>Your code is: {}</p>",
            "Login Code",
            otp_code="123456",
        )

        self.assertEqual(text, "Your code is: 123456")
        self.assertEqual(html, "<p>Your code is: 123456</p>")

        message = service._apply_sms_template(
            "otp_login", "Your code is: {}", otp_code="654321"
        )

        self.assertEqual(message, "Your code is: 654321")

    @patch("core.services.communication_service.send_sendgrid_email")
    def test_email_remains_unchanged(self, mock_sendgrid):
        """CRITICAL: Verify that email functionality remains completely unchanged."""
        mock_sendgrid.return_value = 202

        service = CommunicationService()

        result = service.send_email(
            to_emails=["user1@example.com", "user2@example.com"],
            subject="Test Subject",
            text_content="Plain text",
            html_content="<h1>HTML content</h1>",
            from_email="sender@example.com",
            reply_to="reply@example.com",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.service_used, "sendgrid")

        mock_sendgrid.assert_called_once_with(
            to_emails=["user1@example.com", "user2@example.com"],
            subject="Test Subject",
            text_content="Plain text",
            html_content="<h1>HTML content</h1>",
            from_email="sender@example.com",
            reply_to="reply@example.com",
        )
