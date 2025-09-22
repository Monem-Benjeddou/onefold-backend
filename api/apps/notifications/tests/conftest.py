"""
Pytest configuration and fixtures for notifications app testing.

This file provides comprehensive SMS mocking fixtures that automatically prevent
actual SMS API calls during testing while maintaining realistic behavior.

Key Features:
- Automatic SMS mocking for all notification tests
- Configurable mock behaviors for different test scenarios
- Test isolation and cleanup
- Performance optimized for fast test execution
- Manual testing commands remain unaffected
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from django.test import override_settings
import logging


SMS_BEHAVIOR_CONFIGS = {
    "all_success": {
        "auth_success": True,
        "sms_success": True,
        "rate_limit": False,
        "network_error": False,
    },
    "complete_failure": {
        "auth_success": False,
        "sms_success": False,
        "rate_limit": False,
        "network_error": False,
    },
    "rate_limited": {
        "auth_success": True,
        "sms_success": False,
        "rate_limit": True,
        "network_error": False,
    },
    "network_error": {
        "auth_success": False,
        "sms_success": False,
        "rate_limit": False,
        "network_error": True,
    },
    "auth_failure": {
        "auth_success": False,
        "sms_success": False,
        "rate_limit": False,
        "network_error": False,
    },
}


def reset_global_mocks():
    """Reset any global mock states."""
    pass


logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def mock_sms_for_all_tests(request):
    """
    Automatically mock SMS services for ALL tests to prevent actual API calls.

    This fixture is applied automatically (autouse=True) to every test in the
    notifications app, ensuring no test accidentally makes real SMS API calls.

    The mock provides realistic responses and tracks calls for validation.

    Tests can use @pytest.mark.no_sms_mock to disable this for validation testing.
    """

    if hasattr(request, "node") and request.node.get_closest_marker("no_sms_mock"):
        yield {}
        return

    def create_mock_requests_response(url, **kwargs):
        """Create appropriate mock response based on URL"""
        response = Mock()
        if "keycloak.neons.sa" in url and "protocol/openid-connect/token" in url:
            response.status_code = 200
            response.text = "Authentication successful"
            response.json.return_value = {
                "access_token": "mock_access_token_12345",
                "expires_in": 300,
                "token_type": "Bearer",
            }
        elif "client-credentials" in url:
            response.status_code = 200
            response.text = "Authentication successful"
            response.json.return_value = {
                "access_token": "mock_access_token_12345",
                "expires_in": 300,
                "token_type": "Bearer",
            }
        elif "SMS" in url or "sms" in url:
            response.status_code = 200
            response.text = "SMS sent successfully"
            response.json.return_value = {"isSent": True}
        else:
            response.status_code = 404
            response.text = "Not Found"
        return response

    with (
        patch(
            "apps.notifications.services.neons_sms_service.requests.post",
            side_effect=create_mock_requests_response,
        ) as mock_requests,
        patch("core.tasks.sms.send_sms_task.delay") as mock_sms_task,
        patch(
            "apps.notifications.services.neons_sms_service.NeonsSMSService.send_sms",
            return_value={"success": True, "response": {"isSent": True}},
        ) as mock_neons_service,
    ):

        yield {
            "mock_requests": mock_requests,
            "mock_sms_task": mock_sms_task,
            "mock_neons_service": mock_neons_service,
        }

    reset_global_mocks()


@pytest.fixture
def mock_sms_success():
    """
    SMS mock fixture that always succeeds.
    Use this for tests that need guaranteed SMS success.
    """
    with patch("core.tasks.sms.send_sms_task.delay") as mock:
        mock.return_value = Mock()
        yield mock


@pytest.fixture
def mock_sms_failure():
    """
    SMS mock fixture that always fails.
    Use this for tests that need to verify failure handling.
    """
    with patch("core.tasks.sms.send_sms_task.delay") as mock:
        mock.side_effect = Exception("SMS task failed")
        yield mock


@pytest.fixture
def mock_sms_rate_limited():
    """
    SMS mock fixture that simulates rate limiting.
    Use this for tests that need to verify rate limit handling.
    """

    def mock_rate_limited(*args, **kwargs):
        raise Exception("Rate limit exceeded")

    with patch(
        "core.tasks.sms.send_sms_task.delay", side_effect=mock_rate_limited
    ) as mock:
        yield mock


@pytest.fixture
def mock_sms_network_error():
    """
    SMS mock fixture that simulates network errors.
    Use this for tests that need to verify network error handling.
    """
    import requests

    def mock_network_error(*args, **kwargs):
        raise requests.RequestException("Network error")

    with patch(
        "core.tasks.sms.send_sms_task.delay", side_effect=mock_network_error
    ) as mock:
        yield mock


@pytest.fixture
def mock_sms_auth_failure():
    """
    SMS mock fixture that simulates authentication failures.
    Use this for tests that need to verify auth failure handling.
    """

    def mock_auth_failure_response(url, **kwargs):
        response = Mock()
        if "client-credentials" in url:
            response.status_code = 401
            response.json.return_value = {"error": "Invalid credentials"}
        else:
            response.status_code = 404
        return response

    with patch(
        "apps.notifications.services.neons_sms_service.requests.post",
        side_effect=mock_auth_failure_response,
    ) as mock:
        yield mock


@pytest.fixture
def mock_sms_service_configurable():
    """
    Configurable SMS mock fixture.
    Use this when you need custom mock behavior.

    Usage:
        def test_custom_behavior(mock_sms_service_configurable):
            mock_service = mock_sms_service_configurable(success=True)
            # Your test code here
    """

    def _create_mock_service(success=True):
        with patch("core.tasks.sms.send_sms_task.delay") as mock:
            if success:
                mock.return_value = Mock()
            else:
                mock.side_effect = Exception("SMS task failed")
            return mock

    return _create_mock_service


@pytest.fixture(autouse=True)
def mock_otp_delivery_for_all_tests(request):
    """
    Automatically mock OTP delivery for ALL tests to prevent actual delivery.

    This fixture ensures OTP delivery methods are mocked and don't trigger
    real SMS or email sends during testing.

    Tests can use @pytest.mark.no_sms_mock to disable this for validation testing.
    """

    if hasattr(request, "node") and request.node.get_closest_marker("no_sms_mock"):
        yield {}
        return
    with (
        patch("core.tasks.sms.send_sms_task.delay") as mock_sms_task,
        patch("core.tasks.send_activation_email.delay") as mock_email,
        patch(
            "apps.notifications.services.neons_sms_service.NeonsSMSService.send_sms",
            return_value={"success": True, "response": {"isSent": True}},
        ) as mock_neons_service,
    ):

        mock_sms_task.return_value = Mock()
        mock_email.return_value = Mock()

        yield {
            "mock_sms_task": mock_sms_task,
            "mock_email": mock_email,
            "mock_neons_service": mock_neons_service,
        }


@pytest.fixture
def mock_otp_sms_success():
    """OTP delivery mock that succeeds via SMS."""
    with patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp",
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_otp_sms_failure_email_fallback():
    """OTP delivery mock that fails SMS but succeeds with email fallback."""
    call_count = 0

    def mock_send_otp_with_fallback(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        return call_count > 1

    with patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp",
        side_effect=mock_send_otp_with_fallback,
    ) as mock:
        yield mock


@pytest.fixture
def mock_otp_complete_failure():
    """OTP delivery mock that fails all delivery methods."""
    with patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp",
        return_value=False,
    ) as mock:
        yield mock


@pytest.fixture
def disable_sms_testing():
    """
    Disable SMS configuration for testing edge cases.
    Use this to test behavior when SMS is not configured.
    """
    with override_settings(
        NEONS_SMS_BASE_URL="",
        NEONS_SMS_CLIENT_ID="",
        NEONS_SMS_CLIENT_SECRET="",
        OTP_DELIVERY_METHOD="email",
    ):
        yield


@pytest.fixture
def enable_sms_testing():
    """
    Enable SMS configuration for testing.
    Use this to test behavior when SMS is properly configured.
    """
    with override_settings(
        NEONS_SMS_BASE_URL="https://test.neons.sa",
        NEONS_SMS_CLIENT_ID="test_client_id",
        NEONS_SMS_CLIENT_SECRET="test_client_secret",
        NEONS_SMS_TOKEN_CACHE_TTL=3600,
        OTP_DELIVERY_METHOD="sms",
    ):
        yield


@pytest.fixture
def sms_fallback_enabled():
    """Enable SMS fallback to email for testing."""
    with override_settings(SMS_FALLBACK_TO_EMAIL=True, OTP_DELIVERY_METHOD="sms"):
        yield


@pytest.fixture
def sms_fallback_disabled():
    """Disable SMS fallback to email for testing."""
    with override_settings(SMS_FALLBACK_TO_EMAIL=False, OTP_DELIVERY_METHOD="sms"):
        yield


@pytest.fixture
def user_with_phone(db):
    """Create a test user with a phone number for SMS testing."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(
        email="sms_user@test.com",
        password="testpass123",
        phone_number="+1234567890",
        fullname="SMS Test User",
        username="smsuser",
        is_email_verified=False,
    )


@pytest.fixture
def user_without_phone(db):
    """Create a test user without a phone number for testing edge cases."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(
        email="no_sms_user@test.com",
        password="testpass123",
        fullname="No SMS User",
        username="nosmsuser",
        is_email_verified=False,
    )


@pytest.fixture
def user_with_international_phone(db):
    """Create a test user with an international phone number."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(
        email="intl_user@test.com",
        password="testpass123",
        phone_number="+21626716816",
        fullname="International User",
        username="intluser",
        is_email_verified=False,
    )


@pytest.fixture
def multiple_users_with_phones(db):
    """Create multiple test users with phone numbers for bulk testing."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    users = []

    phone_numbers = [
        "+1111111111",
        "+2222222222",
        "+3333333333",
        "+4444444444",
        "+5555555555",
    ]

    for i, phone in enumerate(phone_numbers):
        user = User.objects.create_user(
            email=f"bulk_user_{i}@test.com",
            password="testpass123",
            phone_number=phone,
            fullname=f"Bulk User {i}",
            username=f"bulkuser{i}",
            is_email_verified=False,
        )
        users.append(user)

    return users


@pytest.fixture(autouse=True)
def clear_sms_cache():
    """Automatically clear SMS-related cache before and after each test."""
    from django.core.cache import cache

    cache.delete("neons_sms_access_token")

    yield

    cache.delete("neons_sms_access_token")


@pytest.fixture
def mock_cache_for_sms():
    """Mock cache for SMS token storage testing."""
    from unittest.mock import patch

    mock_cache = {}

    def mock_get(key, default=None):
        return mock_cache.get(key, default)

    def mock_set(key, value, timeout=None):
        mock_cache[key] = value

    def mock_delete(key):
        mock_cache.pop(key, None)

    with (
        patch(
            "apps.notifications.services.neons_sms_service.cache.get",
            side_effect=mock_get,
        ),
        patch(
            "apps.notifications.services.neons_sms_service.cache.set",
            side_effect=mock_set,
        ),
        patch(
            "apps.notifications.services.neons_sms_service.cache.delete",
            side_effect=mock_delete,
        ),
    ):
        yield mock_cache


@pytest.fixture
def capture_sms_logs():
    """Capture SMS-related log messages for testing."""
    import logging
    from io import StringIO

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger("apps.notifications.services.neons_sms_service")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    yield log_stream

    logger.removeHandler(handler)


@pytest.fixture
def mock_logger():
    """Mock logger for testing log messages."""
    with patch("apps.notifications.services.neons_sms_service.logger") as mock_log:
        yield mock_log


@pytest.fixture
def fast_sms_mock():
    """Ultra-fast SMS mock for performance tests (minimal overhead)."""

    def fast_mock(*args, **kwargs):
        return True

    with (
        patch(
            "apps.notifications.services.neons_sms_service.requests.post"
        ) as mock_post,
        patch("core.tasks.sms.send_sms_task.delay", side_effect=fast_mock),
    ):

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"isSent": True}
        mock_post.return_value = mock_response

        yield mock_post


@pytest.fixture
def integration_sms_mock():
    """
    More realistic SMS mock for integration tests.
    No delays to keep tests fast, but with realistic success patterns.
    """
    call_count = 0

    def realistic_mock(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        return call_count % 10 != 0

    with (
        patch(
            "apps.notifications.services.neons_sms_service.requests.post"
        ) as mock_post,
        patch("core.tasks.sms.send_sms_task.delay", side_effect=realistic_mock),
    ):

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"isSent": True}
        mock_post.return_value = mock_response

        yield mock_post


@pytest.fixture(autouse=True)
def cleanup_sms_mocks():
    """Automatically cleanup SMS mocks after each test."""
    yield

    reset_global_mocks()

    from unittest.mock import _patch

    for patch_obj in list(_patch._active_patches):
        if any(
            sms_related in str(patch_obj)
            for sms_related in ["sms", "SMS", "neons", "otp"]
        ):
            try:
                patch_obj.stop()
            except RuntimeError:
                pass
