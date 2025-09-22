"""
Integration tests for SMS service integration with OTP delivery.

Tests the complete flow from OTP generation to SMS delivery using Neons SMS API
with fallback mechanisms to Twilio and Vonage.
"""

import pytest
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService
from apps.notifications.services import neons_sms_service

User = get_user_model()


@pytest.mark.django_db
class TestSMSIntegration(TestCase):
    """Test SMS service integration with OTP delivery."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            phone_number="+21626716816",
            password="testpass123",
            fullname="Test User",
            username="testuser",
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @override_settings(
        NEONS_SMS_BASE_URL="https://test.neons.sa",
        NEONS_SMS_CLIENT_ID="test_client_id",
        NEONS_SMS_CLIENT_SECRET="test_client_secret",
    )
    @patch("apps.notifications.services.neons_sms_service.requests.post")
    def test_otp_delivery_via_neons_sms(self, mock_post):
        """Test OTP delivery using Neons SMS service."""

        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.text = "Authentication successful"
        auth_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 300,
            "token_type": "Bearer",
        }

        sms_response = Mock()
        sms_response.status_code = 200
        sms_response.text = "SMS sent successfully"
        sms_response.json.return_value = {"isSent": True}

        def mock_post_side_effect(url, **kwargs):
            if "keycloak.neons.sa" in url or "protocol/openid-connect/token" in url:
                return auth_response
            elif "SMS" in url:
                return sms_response
            fallback_mock = Mock(status_code=404)
            fallback_mock.text = "Not Found"
            return fallback_mock

        mock_post.side_effect = mock_post_side_effect

        success = OTPDeliveryService.send_otp(self.user, "123456", "login")

        self.assertTrue(
            success, "OTP delivery should succeed when SMS service is configured"
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @override_settings(
        NEONS_SMS_BASE_URL="https://test.neons.sa",
        NEONS_SMS_CLIENT_ID="test_client_id",
        NEONS_SMS_CLIENT_SECRET="test_client_secret",
    )
    @patch("core.tasks.sms.send_sms_task.delay")
    @patch("apps.notifications.services.neons_sms_service.requests.post")
    def test_otp_delivery_fallback_to_twilio(self, mock_neons_post, mock_sms_task):
        """Test OTP delivery fallback to Twilio when Neons fails."""

        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.text = "Authentication successful"
        auth_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 300,
            "token_type": "Bearer",
        }

        sms_response = Mock()
        sms_response.status_code = 200
        sms_response.text = "SMS not sent"
        sms_response.json.return_value = {"isSent": False}

        def mock_post_side_effect(url, **kwargs):
            if "keycloak.neons.sa" in url or "protocol/openid-connect/token" in url:
                return auth_response
            elif "SMS" in url:
                return sms_response
            fallback_mock = Mock(status_code=404)
            fallback_mock.text = "Not Found"
            return fallback_mock

        mock_neons_post.side_effect = mock_post_side_effect
        mock_sms_task.return_value = True

        success = OTPDeliveryService.send_otp(self.user, "123456", "login")

        self.assertTrue(success)

        mock_sms_task.assert_called_once()

    @override_settings(
        OTP_DELIVERY_METHOD="sms",
        SMS_FALLBACK_TO_EMAIL=True,
        NEONS_SMS_BASE_URL="https://test.neons.sa",
        NEONS_SMS_CLIENT_ID="test_client_id",
        NEONS_SMS_CLIENT_SECRET="test_client_secret",
    )
    @patch("core.tasks.send_activation_email.delay")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_otp_delivery_all_sms_fail_fallback_to_email(
        self, mock_sms_task, mock_email
    ):
        """Test OTP delivery fallback to email when all SMS services fail."""

        mock_sms_task.return_value = None
        mock_email.return_value = Mock()

        success = OTPDeliveryService.send_otp(self.user, "123456", "login")

        self.assertTrue(success)

        mock_sms_task.assert_called_once()

        mock_email.assert_called_once()
        call_kwargs = mock_email.call_args[1]
        self.assertIn("123456", call_kwargs["text_content"])
        self.assertEqual(call_kwargs["to_email"], self.user.email)

    def test_user_validation_for_sms_delivery(self):
        """Test user validation for SMS OTP delivery."""

        is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(self.user)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        user_no_phone = User.objects.create_user(
            email="nophone@example.com",
            phone_number=None,
            password="testpass123",
            fullname="No Phone User",
            username="nophoneuser",
        )

        with override_settings(OTP_DELIVERY_METHOD="sms", SMS_FALLBACK_TO_EMAIL=False):
            is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
                user_no_phone
            )
            self.assertFalse(is_valid)
            self.assertIsNotNone(error)

        with override_settings(OTP_DELIVERY_METHOD="sms", SMS_FALLBACK_TO_EMAIL=True):
            is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
                user_no_phone
            )
            self.assertTrue(is_valid)
            self.assertIsNone(error)

        user_no_contact = User.objects.create_user(
            email="temp@example.com",
            phone_number=None,
            password="testpass123",
            fullname="No Contact User",
            username="nocontactuser",
        )

        user_no_contact.email = ""
        user_no_contact.save()

        with override_settings(OTP_DELIVERY_METHOD="sms"):
            is_valid, error = OTPDeliveryService.validate_user_for_otp_delivery(
                user_no_contact
            )
            self.assertFalse(is_valid)
            self.assertIsNotNone(error)

    def test_delivery_target_display_for_sms(self):
        """Test delivery target display for SMS."""
        with override_settings(OTP_DELIVERY_METHOD="sms"):
            display = OTPDeliveryService.get_delivery_target_display(self.user)
            self.assertIn("SMS to", display)
            self.assertIn("+216****6816", display)

    def test_different_otp_types_message_formatting(self):
        """Test that different OTP types generate appropriate messages."""
        with (
            override_settings(OTP_DELIVERY_METHOD="sms"),
            override_settings(
                NEONS_SMS_BASE_URL="https://test.neons.sa",
                NEONS_SMS_CLIENT_ID="test_client_id",
                NEONS_SMS_CLIENT_SECRET="test_client_secret",
            ),
            patch("core.tasks.sms.send_sms_task.delay") as mock_sms_task,
        ):

            mock_sms_task.return_value = Mock()

            otp_types = ["login", "password_reset", "verification"]

            for otp_type in otp_types:
                mock_sms_task.reset_mock()
                success = OTPDeliveryService.send_otp(self.user, "123456", otp_type)

                self.assertTrue(success)

                mock_sms_task.assert_called_once()

                call_args = mock_sms_task.call_args
                message = call_args[0][0]
                phone_numbers = call_args[0][1]
                task_otp_type = call_args[0][2]

                if otp_type == "login":
                    self.assertIn("login OTP code", message)
                elif otp_type == "password_reset":
                    self.assertIn("password reset OTP code", message)
                elif otp_type == "verification":
                    self.assertIn("verification OTP code", message)

                self.assertIn("123456", message)
                self.assertIn("Kolct", message)
                self.assertEqual(task_otp_type, otp_type)
                self.assertIn("+21626716816", phone_numbers)
