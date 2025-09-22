"""
Pytest fixtures for auth tests - SMS mocking and test optimization.

This module provides comprehensive fixtures for mocking SMS services
to prevent actual SMS sending during tests, ensuring fast and reliable test execution.
"""

import pytest
from unittest.mock import patch, Mock
from django.test import override_settings


@pytest.fixture
def mock_sms_neons():
    """
    Mock the Neons SMS service to prevent actual SMS sending.

    Returns:
        Mock: Mocked send_sms_neons function that returns True by default
    """
    with patch(
        "apps.accounts.auth.services.otp_delivery_service.send_sms_neons"
    ) as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_sms_neons_failure():
    """
    Mock the Neons SMS service to simulate failure scenarios.

    Returns:
        Mock: Mocked send_sms_neons function that returns False
    """
    with patch(
        "apps.accounts.auth.services.otp_delivery_service.send_sms_neons"
    ) as mock:
        mock.return_value = False
        yield mock


@pytest.fixture
def mock_neons_sms_service():
    """
    Mock the NeonsSMSService class for comprehensive testing.

    Returns:
        Mock: Mocked NeonsSMSService instance
    """
    with patch(
        "apps.notifications.services.neons_sms_service.NeonsSMSService"
    ) as mock_class:
        mock_instance = Mock()
        mock_instance.is_configured.return_value = True
        mock_instance.send_sms.return_value = True
        mock_instance.send_otp_sms.return_value = True
        mock_instance.health_check.return_value = {
            "service": "Neons SMS",
            "status": "healthy",
            "configured": True,
        }
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_neons_requests():
    """
    Mock HTTP requests to Neons SMS API to prevent external API calls.

    Returns:
        Mock: Mocked requests.post function
    """
    with patch(
        "apps.notifications.services.neons_sms_service.requests.post"
    ) as mock_post:

        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {"token": "test_access_token"}

        sms_response = Mock()
        sms_response.status_code = 200
        sms_response.json.return_value = {"isSent": True}

        def mock_post_side_effect(url, **kwargs):
            if "identity/client-credentials" in url or "auth/client-credentials" in url:
                return auth_response
            elif "SMS" in url or "sms" in url:
                return sms_response
            return Mock(status_code=404)

        mock_post.side_effect = mock_post_side_effect
        yield mock_post


@pytest.fixture
def mock_email_delivery():
    """
    Mock email delivery to prevent actual email sending.

    Returns:
        Mock: Mocked send_activation_email.delay function
    """
    with patch("core.tasks.send_activation_email.delay") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_otp_delivery_service():
    """
    Mock the entire OTPDeliveryService for comprehensive testing.

    Returns:
        Mock: Mocked OTPDeliveryService class
    """
    with patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService"
    ) as mock_service:
        mock_service.send_otp.return_value = True
        mock_service.validate_user_for_otp_delivery.return_value = (True, None)
        mock_service.get_delivery_method.return_value = "sms"
        mock_service.get_delivery_target_display.return_value = "SMS to +***"
        yield mock_service


@pytest.fixture
def sms_settings():
    """
    Test settings for SMS delivery method.

    Returns:
        dict: Settings override context manager
    """
    return override_settings(
        OTP_DELIVERY_METHOD="sms",
        NEONS_SMS_BASE_URL="https://test.neons.sa",
        NEONS_SMS_CLIENT_ID="test_client_id",
        NEONS_SMS_CLIENT_SECRET="test_client_secret",
        SMS_FALLBACK_TO_EMAIL=True,
    )


@pytest.fixture
def email_settings():
    """
    Test settings for email delivery method.

    Returns:
        dict: Settings override context manager
    """
    return override_settings(OTP_DELIVERY_METHOD="email", SMS_FALLBACK_TO_EMAIL=True)


@pytest.fixture
def disable_ratelimit():
    """
    Disable rate limiting for tests to ensure consistent execution.

    Returns:
        dict: Settings override context manager
    """
    return override_settings(RATELIMIT_ENABLE=False)


@pytest.fixture
def comprehensive_sms_mock():
    """
    Comprehensive SMS mocking that covers all SMS-related functions.

    This fixture mocks all potential SMS sending functions to ensure
    no actual SMS is sent during tests.

    Returns:
        dict: Dictionary of all mocked SMS functions
    """
    mocks = {}

    with patch(
        "apps.accounts.auth.services.otp_delivery_service.send_sms_neons"
    ) as mock_neons:
        mock_neons.return_value = True
        mocks["neons"] = mock_neons

        with patch("apps.accounts.auth.utils.send_sms") as mock_twilio:
            mock_twilio.return_value = False
            mocks["twilio"] = mock_twilio

            with patch("apps.accounts.auth.utils.send_sms_vonage") as mock_vonage:
                mock_vonage.return_value = False
                mocks["vonage"] = mock_vonage

                with patch("core.tasks.send_activation_email.delay") as mock_email:
                    mock_email.return_value = None
                    mocks["email"] = mock_email

                    with patch(
                        "apps.notifications.services.neons_sms_service.neons_sms_service"
                    ) as mock_service:
                        mock_service.is_configured.return_value = True
                        mock_service.send_sms.return_value = True
                        mock_service.send_otp_sms.return_value = True
                        mocks["service"] = mock_service

                        yield mocks


@pytest.fixture
def fast_test_environment():
    """
    Complete fast test environment setup that mocks all external dependencies.

    This fixture combines all necessary mocks for fast test execution:
    - SMS services mocked
    - Email services mocked
    - Rate limiting disabled
    - External API calls prevented

    Returns:
        dict: Complete environment setup
    """
    with override_settings(
        RATELIMIT_ENABLE=False,
        OTP_DELIVERY_METHOD="sms",
        NEONS_SMS_BASE_URL="https://test.neons.sa",
        NEONS_SMS_CLIENT_ID="test_client_id",
        NEONS_SMS_CLIENT_SECRET="test_client_secret",
    ):
        with patch(
            "apps.accounts.auth.services.otp_delivery_service.send_sms_neons"
        ) as mock_sms:
            mock_sms.return_value = True

            with patch("core.tasks.send_activation_email.delay") as mock_email:
                mock_email.return_value = None

                with patch(
                    "apps.notifications.services.neons_sms_service.requests.post"
                ) as mock_requests:

                    auth_response = Mock()
                    auth_response.status_code = 200
                    auth_response.json.return_value = {"token": "test_token"}

                    sms_response = Mock()
                    sms_response.status_code = 200
                    sms_response.json.return_value = {"isSent": True}

                    def side_effect(url, **kwargs):
                        if "client-credentials" in url:
                            return auth_response
                        elif "SMS" in url:
                            return sms_response
                        return Mock(status_code=404)

                    mock_requests.side_effect = side_effect

                    yield {
                        "sms": mock_sms,
                        "email": mock_email,
                        "requests": mock_requests,
                    }


def pytest_configure(config):
    """Configure pytest with custom markers for performance testing."""
    config.addinivalue_line(
        "markers", "sms: mark test as SMS-related (automatically mocked)"
    )
    config.addinivalue_line("markers", "fast: mark test as requiring fast execution")
    config.addinivalue_line("markers", "integration: mark test as integration test")


@pytest.fixture(autouse=True)
def auto_mock_sms(request):
    """
    Automatically mock SMS services for tests marked with @pytest.mark.sms.

    This fixture ensures that any test marked with @pytest.mark.sms will
    automatically have SMS services mocked without requiring manual setup.
    """
    if request.node.get_closest_marker("sms"):
        with patch(
            "apps.accounts.auth.services.otp_delivery_service.send_sms_neons"
        ) as mock:
            mock.return_value = True
            yield mock
    else:
        yield
