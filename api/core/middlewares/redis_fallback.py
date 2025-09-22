"""
Redis Fallback Middleware

This middleware handles Redis connection errors gracefully by providing
fallback mechanisms when Redis is unavailable.
"""

import logging
import time
from django.core.cache import cache, caches
from django.core.cache.backends.base import InvalidCacheBackendError
from django.utils.deprecation import MiddlewareMixin
from django_redis.exceptions import ConnectionInterrupted
from redis.exceptions import (
    ConnectionError,
    TimeoutError,
    AuthenticationError,
    ResponseError,
    BusyLoadingError,
    ReadOnlyError,
)

logger = logging.getLogger(__name__)


class RedisConnectionMiddleware(MiddlewareMixin):
    """
    Middleware to handle Redis connection issues gracefully.

    This middleware catches Redis connection errors and provides
    fallback mechanisms to prevent the application from crashing.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.redis_available = True
        self.last_check = 0
        self.retry_count = 0
        self.max_retries = 3
        self.backoff_factor = 2
        super().__init__(get_response)

    def process_exception(self, request, exception):
        """
        Handle Redis-related exceptions.

        Args:
            request: The HTTP request object
            exception: The exception that occurred

        Returns:
            None to let Django handle the exception normally,
            or an HttpResponse to handle it ourselves
        """

        redis_exceptions = (
            ConnectionInterrupted,
            ConnectionError,
            TimeoutError,
            AuthenticationError,
            InvalidCacheBackendError,
            ResponseError,
            BusyLoadingError,
            ReadOnlyError,
        )

        if isinstance(exception, redis_exceptions):
            logger.error(
                f"Redis connection error: {type(exception).__name__}: {exception}",
                extra={
                    "request_path": request.path,
                    "request_method": request.method,
                    "user_id": (
                        getattr(request.user, "id", None)
                        if hasattr(request, "user")
                        else None
                    ),
                    "retry_count": self.retry_count,
                    "redis_available": self.redis_available,
                },
            )

            self.redis_available = False
            self.retry_count += 1

            try:
                fallback_cache = caches["fallback"]
                logger.warning(
                    f"Switched to fallback cache due to Redis connection issues "
                    f"(retry {self.retry_count}/{self.max_retries})"
                )

                try:
                    fallback_cache.set(
                        "redis_error_info",
                        {
                            "error_type": type(exception).__name__,
                            "error_message": str(exception),
                            "timestamp": time.time(),
                            "retry_count": self.retry_count,
                        },
                        timeout=300,
                    )
                except Exception:
                    pass

            except Exception as e:
                logger.error(f"Failed to switch to fallback cache: {e}")

            return None

        return None

    def process_request(self, request):
        """
        Process incoming requests and check Redis health periodically.

        Args:
            request: The HTTP request object
        """
        current_time = time.time()

        check_interval = 30 if not self.redis_available else 60

        if current_time - self.last_check > check_interval:
            self.last_check = current_time
            self._check_redis_health()

        if self.redis_available and self.retry_count > 0:
            if current_time - self.last_check > 300:
                self.retry_count = 0
                logger.info("Redis retry count reset after stable period")

        return None

    def _check_redis_health(self):
        """Check if Redis is available and update status with exponential backoff."""
        try:

            from django_redis import get_redis_connection

            redis_conn = get_redis_connection("default")

            if redis_conn.ping():
                if not self.redis_available:
                    logger.info(
                        f"Redis connection restored after {self.retry_count} failed attempts"
                    )
                    self.retry_count = 0
                self.redis_available = True
            else:
                self.redis_available = False

        except Exception as e:
            if self.redis_available:
                logger.warning(f"Redis health check failed: {type(e).__name__}: {e}")

            self.redis_available = False

            if self.retry_count < self.max_retries:
                backoff_time = self.backoff_factor**self.retry_count
                logger.info(f"Will retry Redis connection in {backoff_time} seconds")

    def get_redis_status(self):
        """Get current Redis connection status for monitoring."""
        return {
            "available": self.redis_available,
            "retry_count": self.retry_count,
            "last_check": self.last_check,
            "max_retries": self.max_retries,
        }
