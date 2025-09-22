import time
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status
from django.conf import settings


import sys


try:

    rate_limit_metrics = None
    TOOLBAR_ENABLED = False
except ImportError:
    rate_limit_metrics = None
    TOOLBAR_ENABLED = False

def get_rate_limiter_enabled():
    """Get rate limiter enabled setting"""
    return getattr(settings, 'RATE_LIMITER_ENABLED', True)

def get_rate_limiter_default_rate():
    """Get rate limiter default rate setting"""
    return getattr(settings, 'RATE_LIMITER_DEFAULT_RATE', 5)

def get_rate_limiter_default_period():
    """Get rate limiter default period setting"""
    return getattr(settings, 'RATE_LIMITER_DEFAULT_PERIOD', 1)


def get_client_ip(request, *args, **kwargs):
    """Get client IP address from request"""
    if hasattr(request, "request"):
        request = request.request
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def clear_test_rate_limit_cache():
    """Clear the test rate limit cache. Use this in test setUp/tearDown."""
    if hasattr(sys.modules[__name__], "_test_rate_limit_cache"):
        sys.modules[__name__]._test_rate_limit_cache = {}


def dynamic_rate_limit(key_func=None, default_rate=None, default_period=None):
    """
    Rate limiting decorator that can be applied to views.

    Args:
        key_func: Function to generate cache key. Default uses client IP.
        default_rate: Number of allowed requests per period. Default uses setting.
        default_period: Time period in seconds. Default uses setting.
    """
    if key_func is None:
        key_func = get_client_ip

    # Use settings defaults if not provided
    if default_rate is None:
        default_rate = get_rate_limiter_default_rate()
    if default_period is None:
        default_period = get_rate_limiter_default_period()

    default_rate = int(default_rate)
    default_period = int(default_period)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            if not get_rate_limiter_enabled():
                return view_func(request, *args, **kwargs)

            if getattr(settings, "TESTING", False) and not getattr(
                settings, "_RATE_LIMIT_FORCE_ENABLED", False
            ):
                return view_func(request, *args, **kwargs)

            key = key_func(request, *args, **kwargs)
            cache_key = f"ratelimit:{key}:{view_func.__name__}"

            if getattr(settings, "TESTING", False) and getattr(
                settings, "_RATE_LIMIT_FORCE_ENABLED", False
            ):

                if not hasattr(sys.modules[__name__], "_test_rate_limit_cache"):
                    sys.modules[__name__]._test_rate_limit_cache = {}

                timestamps = sys.modules[__name__]._test_rate_limit_cache.get(
                    cache_key, []
                )
            else:
                timestamps = cache.get(cache_key, [])

            if not isinstance(timestamps, list):
                timestamps = []

            now = time.time()

            timestamps = [
                ts
                for ts in timestamps
                if isinstance(ts, (int, float)) and ts > now - default_period
            ]

            allowed = len(timestamps) < default_rate

            time_remaining = 0
            if timestamps:
                oldest_timestamp = min(timestamps)
                time_remaining = max(0, default_period - (now - oldest_timestamp))

            if TOOLBAR_ENABLED and rate_limit_metrics:
                user_id = None
                if hasattr(request, "user") and hasattr(request.user, "id"):
                    user_id = (
                        str(request.user.id) if request.user.is_authenticated else None
                    )

                rate_limit_metrics.record_rate_limit_check(
                    endpoint=request.path,
                    client_ip=key,
                    user_id=user_id,
                    allowed=allowed,
                    current_count=len(timestamps) + (1 if allowed else 0),
                    limit=default_rate,
                    window_seconds=default_period,
                    time_remaining=time_remaining,
                )

            if not allowed:
                return JsonResponse(
                    {"detail": "Rate limit exceeded"},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            timestamps.append(now)

            if getattr(settings, "TESTING", False) and getattr(
                settings, "_RATE_LIMIT_FORCE_ENABLED", False
            ):
                sys.modules[__name__]._test_rate_limit_cache[cache_key] = timestamps
            else:
                cache.set(cache_key, timestamps, default_period)

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
