"""
Django Silk configuration for profiling and monitoring.

This module configures django-silk for comprehensive request profiling,
SQL query analysis, and performance monitoring in development and staging.
"""

import os
from ..config_loader import get_config_value, get_env_bool
from .debug_config import DEBUG


SILKY_AUTHENTICATION = get_env_bool("SILKY_AUTHENTICATION", True)
SILKY_AUTHORISATION = get_env_bool("SILKY_AUTHORISATION", True)


def silk_permissions(user):
    """
    Custom permissions for Silk access.

    Only allow superuser and staff members to access Silk.
    """
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff


SILKY_PERMISSIONS = silk_permissions


SILKY_MAX_REQUEST_BODY_SIZE = get_config_value("silk.max_request_body_size", 10240)
SILKY_MAX_RESPONSE_BODY_SIZE = get_config_value("silk.max_response_body_size", 10240)


SILKY_META = get_env_bool("SILKY_META", True)


if DEBUG:

    SILKY_INTERCEPT_PERCENT = get_config_value("silk.intercept_percent", 100)
else:

    SILKY_INTERCEPT_PERCENT = get_config_value("silk.intercept_percent", 10)


def silk_intercept_func(request):
    """
    Custom logic for when to intercept requests.

    This function allows fine-grained control over which requests to profile.
    """

    if request.path.startswith(("/health/", "/status/", "/deploy-", "/ok/")):
        return False

    if request.path.startswith("/admin/static/"):
        return False

    if request.path.startswith("/media/"):
        return False

    if DEBUG:
        return True

    return request.session.get("silk_profiling_enabled", False)


SILKY_INTERCEPT_FUNC = silk_intercept_func if not DEBUG else None


SILKY_PYTHON_PROFILER = get_env_bool("SILKY_PYTHON_PROFILER", DEBUG)
SILKY_PYTHON_PROFILER_BINARY = get_env_bool("SILKY_PYTHON_PROFILER_BINARY", False)
SILKY_PYTHON_PROFILER_EXTENDED_FILE_NAME = get_env_bool(
    "SILKY_PYTHON_PROFILER_EXTENDED_FILE_NAME", True
)


SILKY_PYTHON_PROFILER_RESULT_PATH = get_config_value(
    "silk.profiler_result_path",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "silk_profiles"
    ),
)


SILKY_MAX_RECORDED_REQUESTS = get_config_value("silk.max_recorded_requests", 10000)
SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = get_config_value("silk.check_percent", 10)


SILKY_ANALYZE_QUERIES = get_env_bool("SILKY_ANALYZE_QUERIES", False)


SILKY_EXPLAIN_FLAGS = {
    "format": "JSON",
    "costs": True,
    "buffers": True,
    "verbose": False,
}


SILKY_SENSITIVE_KEYS = {
    "password",
    "token",
    "key",
    "secret",
    "api",
    "signature",
    "private_key",
    "public_key",
    "auth",
    "authorization",
    "otp",
    "pin",
    "ssn",
    "credit_card",
    "cvv",
    "access_token",
    "refresh_token",
    "session_key",
    "csrf_token",
}


SILKY_DYNAMIC_PROFILING = get_config_value("silk.dynamic_profiling", [])


KOLCT_SILK_SETTINGS = {
    "DETECT_N1_QUERIES": get_config_value("silk.detect_n1_queries", True),
    "N1_QUERY_THRESHOLD": get_config_value("silk.n1_query_threshold", 5),
    "SLOW_REQUEST_THRESHOLD": get_config_value("silk.slow_request_threshold", 1.0),
    "HIGH_QUERY_COUNT_THRESHOLD": get_config_value(
        "silk.high_query_count_threshold", 20
    ),
    "MONITOR_CARD_OPERATIONS": get_config_value("silk.monitor_card_operations", True),
    "MONITOR_ENCRYPTION_OPERATIONS": get_config_value(
        "silk.monitor_encryption_operations", True
    ),
    "REPORT_RETENTION_DAYS": get_config_value("silk.report_retention_days", 7),
}


__all__ = [
    "SILKY_AUTHENTICATION",
    "SILKY_AUTHORISATION",
    "SILKY_PERMISSIONS",
    "SILKY_MAX_REQUEST_BODY_SIZE",
    "SILKY_MAX_RESPONSE_BODY_SIZE",
    "SILKY_META",
    "SILKY_INTERCEPT_PERCENT",
    "SILKY_INTERCEPT_FUNC",
    "SILKY_PYTHON_PROFILER",
    "SILKY_PYTHON_PROFILER_BINARY",
    "SILKY_PYTHON_PROFILER_EXTENDED_FILE_NAME",
    "SILKY_PYTHON_PROFILER_RESULT_PATH",
    "SILKY_MAX_RECORDED_REQUESTS",
    "SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT",
    "SILKY_ANALYZE_QUERIES",
    "SILKY_EXPLAIN_FLAGS",
    "SILKY_SENSITIVE_KEYS",
    "SILKY_DYNAMIC_PROFILING",
    "KOLCT_SILK_SETTINGS",
    "silk_permissions",
    "silk_intercept_func",
]
