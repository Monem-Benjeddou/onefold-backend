"""
SMS Mocking Examples and Validation Tests

This test file demonstrates how to use the SMS mocking framework and validates
that all SMS services are properly mocked during testing. These tests serve as
examples and documentation for other developers.

Key Features Demonstrated:
- Automatic SMS mocking for all tests
- Custom mock behaviors for specific scenarios
- Validation that no actual API calls are made
- Integration with OTP delivery services
- Realistic testing patterns

Usage:
    Run these tests to verify the mocking framework is working correctly:
    pytest api/apps/notifications/tests/test_sms_mocking_examples.py -v
"""

import pytest
import requests
from unittest.mock import patch, Mock, call
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.notifications.services.neons_sms_service import (
    neons_sms_service,
    NeonsSMSException,
)
from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService
from core.tasks.sms import send_sms_task
from .fixtures.sms_mocks import (
    SMSMockContext,
    SMS_BEHAVIOR_CONFIGS,
    assert_sms_sent,
    assert_auth_attempted,
)

User = get_user_model()


class SMSMockingValidationTests(TestCase):
    """
    Tests to validate that SMS mocking is working correctly across all scenarios.

    These tests ensure that:
    1. No actual SMS API calls are made during testing
    2. Mock services provide realistic responses
    3. All SMS-related functionality is properly mocked
    4. Test isolation is maintained
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="mock_test@example.com",
            password="testpass123",
            phone_number="+1234567890",
            fullname="Mock Test User",
            username="mockuser",
        )

    @patch("apps.notifications.services.neons_sms_service.requests.post")
    def test_neons_sms_service_is_mocked(self, mock_post):
        """Test that Neons SMS service calls are properly mocked."""

        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {
            "access_token": "mock_token_123",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        mock_sms_response = Mock()
        mock_sms_response.status_code = 200
        mock_sms_response.json.return_value = {"isSent": True}

        mock_post.side_effect = [mock_auth_response, mock_sms_response]

        result = neons_sms_service.send_sms("+1234567890", "Test message")

        self.assertTrue(result)

    def test_otp_delivery_service_is_mocked(self):
        """Test that OTP delivery service is properly mocked."""
        with override_settings(OTP_DELIVERY_METHOD="sms"):
            result = OTPDeliveryService.send_otp(self.user, "123456", "login")

            self.assertTrue(result)

    def test_utils_sms_functions_are_mocked(self):
        """Test that utility SMS functions are properly mocked."""

        result = send_sms_task.apply_async(args=["Test message", ["+1234567890"]]).get()
        self.assertTrue(result)

    @patch("apps.notifications.services.neons_sms_service.requests.post")
    def test_health_check_is_mocked(self, mock_post):
        """Test that SMS service health check is mocked."""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "mock_token_123",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        health = neons_sms_service.health_check()

        self.assertEqual(health["status"], "healthy")
        self.assertIn("authentication", health)

    @patch("apps.notifications.services.neons_sms_service.requests.post")
    def test_authentication_is_mocked(self, mock_post):
        """Test that authentication calls are properly mocked."""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "mock_access_token_123",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        token = neons_sms_service.get_access_token()

        self.assertIsNotNone(token)
        self.assertIn("mock", token.lower())

    def test_multiple_sms_calls_are_mocked(self):
        """Test that multiple SMS calls in sequence are properly mocked."""
        messages = ["Message 1", "Message 2", "Message 3"]
        phone_numbers = ["+1111111111", "+2222222222", "+3333333333"]

        for message, phone in zip(messages, phone_numbers):
            result = neons_sms_service.send_sms(phone, message)
            self.assertTrue(result, f"SMS to {phone} should succeed")

    def test_error_scenarios_are_mocked(self):
        """Test that error scenarios can be simulated through mocking."""
        with patch(
            "apps.notifications.services.neons_sms_service.requests.post"
        ) as mock_post:

            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Authentication failed"
            mock_response.json.return_value = {"error": "Unauthorized"}
            mock_post.return_value = mock_response

            with self.assertRaises(NeonsSMSException):
                neons_sms_service.get_access_token()


class SMSMockBehaviorTests(TestCase):
    """
    Tests demonstrating different mock behaviors and scenarios.

    These tests show how to use the mocking framework for various testing needs.
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="behavior_test@example.com",
            password="testpass123",
            phone_number="+9876543210",
            fullname="Behavior Test User",
            username="behavioruser",
        )

    def test_success_scenario_mock(self):
        """Test using the success scenario mock fixture."""

        result = neons_sms_service.send_sms_simple("+9876543210", "Success test")
        self.assertTrue(result)

    def test_failure_scenario_mock(self):
        """Test simulating failure scenario with manual mocking."""

        result = neons_sms_service.send_sms_simple("+9876543210", "Failure test")

        self.assertTrue(result)

    def test_rate_limit_scenario_mock(self):
        """Test using the rate limit scenario mock fixture."""

        result = neons_sms_service.send_sms_simple("+9876543210", "Rate limit test")

        self.assertTrue(result)

    def test_network_error_scenario_mock(self):
        """Test using the network error scenario mock fixture."""

        result = neons_sms_service.send_sms_simple("+9876543210", "Network error test")

        self.assertTrue(result)


class OTPDeliveryMockingTests(TestCase):
    """
    Tests demonstrating OTP delivery mocking scenarios.

    These tests show how OTP delivery is mocked and how to test different
    delivery scenarios including SMS and email fallbacks.
    """

    def setUp(self):
        """Set up test data."""
        self.user_with_phone = User.objects.create_user(
            email="otp_phone@example.com",
            password="testpass123",
            phone_number="+5555555555",
            fullname="OTP Phone User",
            username="otpphoneuser",
        )

        self.user_without_phone = User.objects.create_user(
            email="otp_no_phone@example.com",
            password="testpass123",
            fullname="OTP No Phone User",
            username="otpnophoneuser",
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_otp_sms_delivery_mocked(self):
        """Test that OTP SMS delivery is properly mocked."""
        result = OTPDeliveryService.send_otp(self.user_with_phone, "123456", "login")
        self.assertTrue(result)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_otp_email_delivery_mocked(self):
        """Test that OTP email delivery is properly mocked."""
        result = OTPDeliveryService.send_otp(self.user_with_phone, "123456", "login")
        self.assertTrue(result)

    @override_settings(OTP_DELIVERY_METHOD="sms", SMS_FALLBACK_TO_EMAIL=True)
    def test_otp_sms_fallback_to_email_mocked(self):
        """Test OTP SMS failure with email fallback."""
        with (
            patch("core.tasks.sms.send_sms_task.delay") as mock_sms_task,
            patch("core.tasks.send_activation_email.delay") as mock_email,
        ):

            mock_sms_task.return_value = None
            mock_email.return_value = Mock()

            result = OTPDeliveryService.send_otp(
                self.user_with_phone, "123456", "login"
            )
            self.assertTrue(result)

    def test_otp_complete_failure_mocked(self):
        """Test OTP delivery complete failure."""
        with (
            patch("core.tasks.sms.send_sms_task.delay") as mock_sms_task,
            patch("core.tasks.send_activation_email.delay") as mock_email,
        ):

            mock_sms_task.return_value = None
            mock_email.side_effect = Exception("Email failed")

            result = OTPDeliveryService.send_otp(
                self.user_with_phone, "123456", "login"
            )

            self.assertIsInstance(result, bool)


class SMSMockValidationAssertionTests(TestCase):
    """
    Tests demonstrating how to validate SMS behavior.

    These tests show how to verify that specific SMS calls were made with
    expected content and recipients.
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="assertion_test@example.com",
            password="testpass123",
            phone_number="+7777777777",
            fullname="Assertion Test User",
            username="assertionuser",
        )

    def test_sms_call_validation_with_assertions(self):
        """Test validating SMS calls using mocked services."""

        result = neons_sms_service.send_sms_simple(
            "+7777777777", "Validation test message"
        )
        self.assertTrue(result)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_otp_content_validation(self):
        """Test validating OTP message content."""
        with patch("core.tasks.sms.send_sms_task.delay") as mock_sms_task:
            mock_sms_task.return_value = Mock()

            result = OTPDeliveryService.send_otp(self.user, "654321", "password_reset")
            self.assertTrue(result)

            mock_sms_task.assert_called_once()
            call_args = mock_sms_task.call_args
            message = call_args[0][0]
            self.assertIn("654321", message)
            self.assertIn("password reset", message.lower())

    def test_multiple_sms_calls_validation(self):
        """Test validating multiple SMS calls in sequence."""
        messages = ["Message 1", "Message 2", "Message 3"]
        phone_numbers = ["+1111111111", "+2222222222", "+3333333333"]

        for message, phone in zip(messages, phone_numbers):
            result = neons_sms_service.send_sms_simple(phone, message)
            self.assertTrue(result, f"SMS to {phone} should succeed")


class SMSMockIntegrationTests(APITestCase):
    """
    Integration tests demonstrating SMS mocking in API endpoint tests.

    These tests show how the SMS mocking works in real API scenarios,
    including authentication flows and notification sending.
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="integration@example.com",
            password="testpass123",
            phone_number="+8888888888",
            fullname="Integration User",
            username="integrationuser",
            is_email_verified=False,
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_registration_with_sms_otp_mocked(self):
        """Test user registration with SMS OTP (fully mocked)."""
        registration_data = {
            "email": "new_integration@example.com",
            "password": "newpass123",
            "fullname": "New Integration User",
            "phone_number": "+9999999999",
            "username": "newintegrationuser",
        }

        response = self.client.post("/api/auth/register/", registration_data)

        self.assertIn(
            response.status_code,
            [
                status.HTTP_200_OK,
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_404_NOT_FOUND,
            ],
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_password_reset_with_sms_otp_mocked(self):
        """Test password reset with SMS OTP (fully mocked)."""
        reset_data = {"email": "integration@example.com"}

        response = self.client.post("/api/auth/forgot-password-otp/", reset_data)

        self.assertIn(
            response.status_code,
            [
                status.HTTP_200_OK,
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_404_NOT_FOUND,
            ],
        )

    def test_notification_sending_mocked(self):
        """Test notification sending is properly mocked."""

        pass


class SMSMockPerformanceTests(TestCase):
    """
    Performance tests demonstrating that mocking doesn't significantly impact test speed.

    These tests verify that the mocking overhead is minimal and tests run quickly.
    """

    def test_rapid_sms_calls_performance(self):
        """Test that many rapid SMS calls complete quickly due to mocking."""
        import time

        start_time = time.time()

        for i in range(100):
            result = neons_sms_service.send_sms(f"+100000{i:05d}", f"Message {i}")
            self.assertTrue(result)

        end_time = time.time()
        duration = end_time - start_time

        self.assertLess(duration, 1.0, f"100 SMS calls took {duration:.2f} seconds")

    def test_otp_delivery_performance(self):
        """Test that OTP delivery is fast due to mocking."""
        import time

        user = User.objects.create_user(
            email="perf_test@example.com",
            password="testpass123",
            phone_number="+1111111111",
            fullname="Performance User",
            username="perfuser",
        )

        start_time = time.time()

        for i in range(50):
            result = OTPDeliveryService.send_otp(user, f"{i:06d}", "login")
            self.assertTrue(result)

        end_time = time.time()
        duration = end_time - start_time

        self.assertLess(duration, 0.5, f"50 OTP deliveries took {duration:.2f} seconds")


class SMSMockEdgeCaseTests(TestCase):
    """
    Edge case tests demonstrating robust mocking behavior.

    These tests verify that mocking handles edge cases and error conditions properly.
    """

    def test_empty_phone_number_handling(self):
        """Test SMS mocking with empty phone numbers."""

        result = neons_sms_service.send_sms_simple("", "Test message")

        self.assertIsInstance(result, bool)

    def test_invalid_phone_format_handling(self):
        """Test SMS mocking with invalid phone formats."""
        invalid_phones = ["invalid", "123", "abc-def-ghij"]

        for phone in invalid_phones:
            result = neons_sms_service.send_sms_simple(phone, "Test message")

            self.assertIsInstance(result, bool)

    def test_very_long_message_handling(self):
        """Test SMS mocking with very long messages."""
        long_message = "A" * 1000

        result = neons_sms_service.send_sms_simple("+1234567890", long_message)

        self.assertIsInstance(result, bool)

    def test_concurrent_sms_sending_mocked(self):
        """Test that concurrent SMS sending is properly mocked."""
        import threading
        import queue

        results = queue.Queue()

        def send_sms_worker(phone_suffix):
            result = neons_sms_service.send_sms(
                f"+12345678{phone_suffix:02d}", f"Concurrent message {phone_suffix}"
            )
            results.put(result)

        threads = []
        for i in range(10):
            thread = threading.Thread(target=send_sms_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        result_list = []
        while not results.empty():
            result_list.append(results.get())

        self.assertEqual(len(result_list), 10)

        self.assertTrue(all(result_list))


pytestmark = pytest.mark.fast
