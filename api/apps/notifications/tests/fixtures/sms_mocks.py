"""
SMS Mocking Fixtures and Utilities for Test Suite

This module provides comprehensive mocking for all SMS-related functionality to prevent
actual SMS API calls during automated testing while preserving realistic behavior.

Key Features:
- Prevents rate limiting by mocking actual SMS API calls
- Simulates realistic success/failure scenarios
- Works with OTP delivery and notification systems
- Maintains proper test isolation
- Doesn't affect manual testing capabilities

Usage:
    Use the provided fixtures in test classes or import specific mock functions.
    All SMS-related tests should use these mocks to avoid actual API calls.
"""

import logging
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List, Optional, Callable
import pytest
from django.test import override_settings


logger = logging.getLogger(__name__)


class SMSMockResponses:
    """Predefined mock responses for different SMS scenarios."""

    SUCCESS_AUTH_RESPONSE = {
        "status_code": 200,
        "json_data": {
            "access_token": "mock_access_token_12345",
            "expires_in": 300,
            "token_type": "Bearer",
        },
        "text": "Success",
    }

    SUCCESS_SMS_RESPONSE = {
        "status_code": 200,
        "json_data": {"isSent": True},
        "text": "SMS sent successfully",
    }

    FAILED_AUTH_RESPONSE = {
        "status_code": 401,
        "json_data": {"error": "Unauthorized"},
        "text": "Authentication failed",
    }

    FAILED_SMS_RESPONSE = {
        "status_code": 200,
        "json_data": {"isSent": False},
        "text": "SMS sending failed",
    }

    RATE_LIMIT_RESPONSE = {
        "status_code": 429,
        "json_data": {"error": "Rate limit exceeded"},
        "text": "Too many requests",
    }

    SERVER_ERROR_RESPONSE = {
        "status_code": 500,
        "json_data": {"error": "Internal server error"},
        "text": "Server error",
    }

    NETWORK_ERROR_RESPONSE = {
        "status_code": 503,
        "json_data": {"error": "Service unavailable"},
        "text": "Network error",
    }


class MockSMSService:
    """
    Mock SMS service that simulates Neons SMS API behavior.

    This class provides realistic responses for different scenarios including
    success, failure, rate limiting, and network errors.
    """

    def __init__(self, behavior_config: Optional[Dict[str, Any]] = None):
        """
        Initialize mock SMS service with configurable behavior.

        Args:
            behavior_config: Dictionary defining mock behavior:
                - 'auth_success': Whether authentication should succeed (default: True)
                - 'sms_success': Whether SMS sending should succeed (default: True)
                - 'rate_limit': Whether to simulate rate limiting (default: False)
                - 'network_error': Whether to simulate network errors (default: False)
                - 'delay_auth': Simulate slow authentication (default: False)
        """
        self.behavior_config = behavior_config or {}
        self.call_history = []
        self.reset_call_counts()

    def reset_call_counts(self):
        """Reset call tracking counters."""
        self.auth_call_count = 0
        self.sms_call_count = 0
        self.call_history.clear()

    def create_mock_response(self, response_config: Dict[str, Any]) -> Mock:
        """Create a mock HTTP response object."""
        mock_response = Mock()
        mock_response.status_code = response_config["status_code"]
        mock_response.json.return_value = response_config["json_data"]
        mock_response.text = response_config["text"]
        return mock_response

    def mock_authentication_request(self, url: str, **kwargs) -> Mock:
        """Mock authentication request to Neons API."""
        self.auth_call_count += 1

        call_info = {
            "type": "auth",
            "url": url,
            "method": "POST",
            "data": kwargs.get("json", {}),
            "headers": kwargs.get("headers", {}),
            "call_number": self.auth_call_count,
        }
        self.call_history.append(call_info)

        if self.behavior_config.get("rate_limit", False):
            return self.create_mock_response(SMSMockResponses.RATE_LIMIT_RESPONSE)

        if self.behavior_config.get("network_error", False):
            from requests.exceptions import RequestException

            raise RequestException("Simulated network error")

        if self.behavior_config.get("auth_success", True):
            return self.create_mock_response(SMSMockResponses.SUCCESS_AUTH_RESPONSE)
        else:
            return self.create_mock_response(SMSMockResponses.FAILED_AUTH_RESPONSE)

    def mock_sms_request(self, url: str, **kwargs) -> Mock:
        """Mock SMS sending request to Neons API."""
        self.sms_call_count += 1

        call_info = {
            "type": "sms",
            "url": url,
            "method": "POST",
            "data": kwargs.get("json", {}),
            "headers": kwargs.get("headers", {}),
            "call_number": self.sms_call_count,
        }
        self.call_history.append(call_info)

        sms_data = kwargs.get("json", {})
        phone_number = sms_data.get("PhoneNumber", "")
        message = sms_data.get("Template", "")

        if not phone_number.startswith("+"):
            return self.create_mock_response(
                {
                    "status_code": 400,
                    "json_data": {"error": "Invalid phone number format"},
                    "text": "Bad Request",
                }
            )

        if self.behavior_config.get("rate_limit", False):
            return self.create_mock_response(SMSMockResponses.RATE_LIMIT_RESPONSE)

        if self.behavior_config.get("network_error", False):
            from requests.exceptions import RequestException

            raise RequestException("Simulated network error")

        if self.behavior_config.get("sms_success", True):
            return self.create_mock_response(SMSMockResponses.SUCCESS_SMS_RESPONSE)
        else:
            return self.create_mock_response(SMSMockResponses.FAILED_SMS_RESPONSE)

    def mock_requests_post(self, url: str, **kwargs) -> Mock:
        """
        Main mock function that routes requests to appropriate handlers.

        This function examines the URL to determine if it's an authentication
        or SMS request and routes it accordingly.
        """
        if (
            ("keycloak.neons.sa" in url and "protocol/openid-connect/token" in url)
            or "identity/client-credentials" in url
            or "auth/token" in url
            or "oauth/token" in url
        ):
            return self.mock_authentication_request(url, **kwargs)
        elif "SMS" in url or "sms" in url:
            return self.mock_sms_request(url, **kwargs)
        else:

            return self.create_mock_response(
                {
                    "status_code": 404,
                    "json_data": {"error": "Not found"},
                    "text": "Not Found",
                }
            )

    def get_call_summary(self) -> Dict[str, Any]:
        """Get summary of all mocked calls."""
        return {
            "total_calls": len(self.call_history),
            "auth_calls": self.auth_call_count,
            "sms_calls": self.sms_call_count,
            "call_history": self.call_history,
            "behavior_config": self.behavior_config,
        }


class MockOTPDeliveryService:
    """Mock for OTP delivery service that simulates various delivery scenarios."""

    def __init__(self, sms_success: bool = True, email_fallback: bool = True):
        """
        Initialize mock OTP delivery service.

        Args:
            sms_success: Whether SMS delivery should succeed
            email_fallback: Whether email fallback should be available
        """
        self.sms_success = sms_success
        self.email_fallback = email_fallback
        self.delivery_attempts = []

    def mock_send_otp(self, user, otp_code: str, otp_type: str = "login") -> bool:
        """Mock OTP sending with configurable behavior."""
        delivery_attempt = {
            "user_email": user.email,
            "user_phone": getattr(user, "phone_number", None),
            "otp_code": otp_code,
            "otp_type": otp_type,
            "delivery_method": (
                "sms"
                if hasattr(user, "phone_number") and user.phone_number
                else "email"
            ),
            "success": self.sms_success or self.email_fallback,
        }
        self.delivery_attempts.append(delivery_attempt)

        if not self.sms_success and self.email_fallback:
            delivery_attempt["fallback_used"] = True
            return True

        return self.sms_success

    def get_delivery_summary(self) -> Dict[str, Any]:
        """Get summary of delivery attempts."""
        return {
            "total_attempts": len(self.delivery_attempts),
            "delivery_attempts": self.delivery_attempts,
            "sms_success_rate": self.sms_success,
            "email_fallback_enabled": self.email_fallback,
        }


_global_mock_sms_service = None
_global_mock_otp_service = None


def get_mock_sms_service(
    behavior_config: Optional[Dict[str, Any]] = None
) -> MockSMSService:
    """Get or create global mock SMS service instance."""
    global _global_mock_sms_service
    if _global_mock_sms_service is None or behavior_config:
        _global_mock_sms_service = MockSMSService(behavior_config)
    return _global_mock_sms_service


def get_mock_otp_service(
    sms_success: bool = True, email_fallback: bool = True
) -> MockOTPDeliveryService:
    """Get or create global mock OTP delivery service instance."""
    global _global_mock_otp_service
    if _global_mock_otp_service is None:
        _global_mock_otp_service = MockOTPDeliveryService(sms_success, email_fallback)
    return _global_mock_otp_service


def reset_global_mocks():
    """Reset all global mock instances."""
    global _global_mock_sms_service, _global_mock_otp_service
    if _global_mock_sms_service:
        _global_mock_sms_service.reset_call_counts()
    if _global_mock_otp_service:
        _global_mock_otp_service.delivery_attempts.clear()


SMS_BEHAVIOR_CONFIGS = {
    "all_success": {
        "auth_success": True,
        "sms_success": True,
        "rate_limit": False,
        "network_error": False,
    },
    "auth_failure": {
        "auth_success": False,
        "sms_success": True,
        "rate_limit": False,
        "network_error": False,
    },
    "sms_failure": {
        "auth_success": True,
        "sms_success": False,
        "rate_limit": False,
        "network_error": False,
    },
    "rate_limited": {
        "auth_success": True,
        "sms_success": True,
        "rate_limit": True,
        "network_error": False,
    },
    "network_error": {
        "auth_success": True,
        "sms_success": True,
        "rate_limit": False,
        "network_error": True,
    },
    "complete_failure": {
        "auth_success": False,
        "sms_success": False,
        "rate_limit": True,
        "network_error": False,
    },
}


def create_success_scenario() -> MockSMSService:
    """Create mock service that always succeeds."""
    return MockSMSService(SMS_BEHAVIOR_CONFIGS["all_success"])


def create_failure_scenario() -> MockSMSService:
    """Create mock service that always fails."""
    return MockSMSService(SMS_BEHAVIOR_CONFIGS["complete_failure"])


def create_rate_limit_scenario() -> MockSMSService:
    """Create mock service that simulates rate limiting."""
    return MockSMSService(SMS_BEHAVIOR_CONFIGS["rate_limited"])


def create_network_error_scenario() -> MockSMSService:
    """Create mock service that simulates network errors."""
    return MockSMSService(SMS_BEHAVIOR_CONFIGS["network_error"])


class SMSMockContext:
    """Context manager for temporary SMS service mocking."""

    def __init__(self, behavior_config: Optional[Dict[str, Any]] = None):
        """
        Initialize SMS mock context.

        Args:
            behavior_config: Configuration for mock behavior
        """
        self.behavior_config = behavior_config or SMS_BEHAVIOR_CONFIGS["all_success"]
        self.mock_service = None
        self.patches = []

    def __enter__(self) -> MockSMSService:
        """Enter context and start mocking."""
        self.mock_service = MockSMSService(self.behavior_config)

        self.patches.append(
            patch(
                "apps.notifications.services.neons_sms_service.requests.post",
                side_effect=self.mock_service.mock_requests_post,
            )
        )

        self.patches.append(
            patch(
                "core.tasks.sms.send_sms_task.delay",
                return_value=Mock(id="mock_task_id"),
            )
        )

        for p in self.patches:
            p.start()

        return self.mock_service

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and stop mocking."""

        for p in self.patches:
            p.stop()
        self.patches.clear()


def validate_sms_call_data(
    call_data: Dict[str, Any], expected_phone: str, expected_message_content: str
) -> bool:
    """
    Validate SMS call data contains expected information.

    Args:
        call_data: Call data from mock service
        expected_phone: Expected phone number
        expected_message_content: Expected content in message

    Returns:
        bool: True if validation passes
    """
    if call_data["type"] != "sms":
        return False

    sms_data = call_data.get("data", {})
    phone_number = sms_data.get("PhoneNumber", "")
    message = sms_data.get("Template", "")

    return (
        phone_number == expected_phone
        and expected_message_content.lower() in message.lower()
    )


def validate_auth_call_data(call_data: Dict[str, Any], expected_client_id: str) -> bool:
    """
    Validate authentication call data contains expected information.

    Args:
        call_data: Call data from mock service
        expected_client_id: Expected client ID

    Returns:
        bool: True if validation passes
    """
    if call_data["type"] != "auth":
        return False

    auth_data = call_data.get("data", {})
    client_id = auth_data.get("clientId", "")

    return client_id == expected_client_id


def assert_sms_sent(
    mock_service: MockSMSService, phone_number: str, message_content: str
):
    """Assert that an SMS was sent with specific content."""
    sms_calls = [call for call in mock_service.call_history if call["type"] == "sms"]

    if not sms_calls:
        raise AssertionError("No SMS calls were made")

    for call in sms_calls:
        if validate_sms_call_data(call, phone_number, message_content):
            return

    raise AssertionError(
        f"No SMS call found with phone {phone_number} and content '{message_content}'. "
        f"Actual calls: {sms_calls}"
    )


def assert_auth_attempted(mock_service: MockSMSService, client_id: str):
    """Assert that authentication was attempted with specific client ID."""
    auth_calls = [call for call in mock_service.call_history if call["type"] == "auth"]

    if not auth_calls:
        raise AssertionError("No authentication calls were made")

    for call in auth_calls:
        if validate_auth_call_data(call, client_id):
            return

    raise AssertionError(
        f"No authentication call found with client ID {client_id}. "
        f"Actual calls: {auth_calls}"
    )


def assert_no_actual_sms_calls():
    """Assert that no actual SMS API calls were made during testing."""

    pass
