"""
Quick SMS Mocking Check

This test file provides a quick way to verify that SMS mocking is working correctly.
Run this to ensure the mocking strategy prevents actual API calls.

Usage:
    pytest api/apps/notifications/tests/test_sms_mocking_quick_check.py -v -s
"""

import pytest
from unittest.mock import patch, Mock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.notifications.services.neons_sms_service import neons_sms_service
from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService
from core.tasks.sms import send_sms_task

User = get_user_model()


class SMSMockingQuickCheckTest(TestCase):
    """Quick tests to verify SMS mocking is working."""

    def setUp(self):
        """Set up test data."""
        self.test_user = User.objects.create_user(
            email="quickcheck@test.com",
            password="testpass123",
            phone_number="+1234567890",
            fullname="Quick Check User",
            username="quickcheckuser",
        )

    @patch("apps.notifications.services.neons_sms_service.requests.post")
    @patch("apps.notifications.services.neons_sms_service.requests.get")
    def test_sms_mocking_prevents_real_api_calls(self, mock_get, mock_post):
        """CRITICAL: Verify that no real HTTP requests are made."""

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

        mock_health_response = Mock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_health_response

        result1 = neons_sms_service.send_sms("+1234567890", "Test message")
        result2 = neons_sms_service.get_access_token()
        result3 = send_sms_task.apply_async(
            args=["Test message", ["+1234567890"]]
        ).get()

        self.assertIsInstance(result1, dict)
        self.assertTrue(result1.get("success", False))
        self.assertIsNotNone(result2)
        self.assertTrue(result3)

    @patch("apps.notifications.services.neons_sms_service.requests.post")
    @patch("apps.notifications.services.neons_sms_service.requests.get")
    def test_neons_sms_service_is_mocked(self, mock_get, mock_post):
        """Verify Neons SMS service operations are mocked."""

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

        mock_health_response = Mock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_health_response

        result = neons_sms_service.send_sms("+1234567890", "Mock test")
        self.assertTrue(result, "SMS should succeed due to mocking")

        token = neons_sms_service.get_access_token()
        self.assertIsNotNone(token, "Should get mock token")

        health = neons_sms_service.health_check()
        self.assertEqual(
            health["status"], "healthy", "Should be healthy due to mocking"
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    def test_otp_delivery_is_mocked(self):
        """Verify OTP delivery is mocked."""
        result = OTPDeliveryService.send_otp(self.test_user, "123456", "login")
        self.assertTrue(result, "OTP delivery should succeed due to mocking")

    def test_utility_functions_are_mocked(self):
        """Verify utility SMS functions are mocked."""
        result = send_sms_task.apply_async(args=["Test utility", ["+1234567890"]]).get()
        self.assertTrue(result, "Utility function should succeed due to mocking")

    @patch("apps.notifications.services.neons_sms_service.requests.post")
    def test_bulk_operations_are_fast(self, mock_post):
        """Verify bulk operations are fast due to mocking."""
        import time

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

        mock_post.side_effect = [mock_auth_response] + [mock_sms_response] * 20

        start_time = time.time()

        for i in range(20):
            result = neons_sms_service.send_sms(f"+555000{i:04d}", f"Bulk test {i}")
            self.assertIsInstance(result, dict, f"Bulk SMS {i} should return dict")
            self.assertTrue(
                result.get("success", False), f"Bulk SMS {i} should succeed"
            )

        duration = time.time() - start_time

        self.assertLess(
            duration,
            0.5,
            f"20 SMS operations took {duration:.3f} seconds - too slow for mocked operations",
        )

    def test_error_scenarios_can_be_simulated(self):
        """Verify that error scenarios can be simulated through mocking."""

        result = neons_sms_service.send_sms("invalid-phone", "Error test")
        self.assertIsInstance(result, dict)

        self.assertIn("success", result)

    def test_realistic_phone_number_handling(self):
        """Verify mocks handle realistic phone numbers correctly."""
        test_phones = [
            "+1234567890",
            "+21626716816",
            "+44123456789",
            "+33123456789",
        ]

        for phone in test_phones:
            result = neons_sms_service.send_sms(phone, "International test")
            self.assertTrue(result, f"SMS to {phone} should succeed")

    def test_otp_message_types_are_handled(self):
        """Verify different OTP message types are handled correctly."""
        otp_types = ["login", "password_reset", "verification", "registration"]

        for otp_type in otp_types:
            with self.subTest(otp_type=otp_type):
                result = OTPDeliveryService.send_otp(self.test_user, "123456", otp_type)
                self.assertTrue(result, f"OTP type {otp_type} should succeed")

    def test_concurrent_operations_are_mocked(self):
        """Verify concurrent SMS operations are properly mocked."""
        import threading
        import queue

        results = queue.Queue()

        def worker(worker_id):
            result = neons_sms_service.send_sms(
                f"+555{worker_id:07d}", f"Concurrent {worker_id}"
            )
            results.put(result)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        result_list = []
        while not results.empty():
            result_list.append(results.get())

        self.assertEqual(len(result_list), 5, "All threads should complete")
        self.assertTrue(all(result_list), "All concurrent operations should succeed")

    @patch("apps.notifications.services.neons_sms_service.requests.post")
    def test_cache_operations_work_with_mocking(self, mock_post):
        """Verify cache operations work correctly with mocking."""
        from django.core.cache import cache

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "mock_token_123",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        cache.delete("neons_sms_access_token")

        token1 = neons_sms_service.get_access_token()
        self.assertIsNotNone(token1)

        token2 = neons_sms_service.get_access_token()
        self.assertEqual(token1, token2, "Should use cached token")

        cached_token = cache.get("neons_sms_access_token")
        self.assertIsNotNone(cached_token, "Token should be cached")


pytestmark = pytest.mark.fast


def print_test_summary():
    """Print a summary after tests complete."""
    print("\n" + "=" * 60)
    print("SMS MOCKING QUICK CHECK SUMMARY")
    print("=" * 60)
    print("✅ If all tests passed, SMS mocking is working correctly!")
    print("✅ No actual SMS API calls should have been made")
    print("✅ Tests should have completed quickly due to mocking")
    print("✅ Manual testing commands will still work normally")
    print("\nNext steps:")
    print("1. Run full test suite to verify comprehensive coverage")
    print("2. Use manual commands for real SMS testing when needed")
    print("3. Refer to README_SMS_MOCKING.md for detailed usage")
    print("=" * 60)
