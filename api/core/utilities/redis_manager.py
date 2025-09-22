"""
Redis Connection Manager and Health Check Utility

This module provides enterprise-grade Redis connection management with:
- Automatic connection health monitoring
- Graceful fallback when Redis is unavailable
- Cache invalidation strategies
- Connection retry logic
- Performance monitoring
"""

import logging
import time
from typing import Optional, Dict, Any, Union, List
from functools import wraps
from django.core.cache import cache
from django.core.cache.backends.base import BaseCache
from django.conf import settings
from django_redis import get_redis_connection
from django_redis.cache import RedisCache
from redis.exceptions import ConnectionError, TimeoutError, RedisError
import redis

logger = logging.getLogger(__name__)


class RedisConnectionManager:
    """
    Manages Redis connections with health monitoring and graceful fallbacks.
    """

    def __init__(self):
        self._last_health_check = 0
        self._health_check_interval = 60
        self._connection_healthy = True
        self._connection_errors = 0
        self._max_connection_errors = 3
        self._retry_attempts = 0
        self._max_retry_attempts = 3
        self._retry_delay = 2.0

    def get_connection(self, alias: str = "default") -> Optional[redis.Redis]:
        """
        Get a Redis connection with health checking and retry logic.

        Args:
            alias: Cache alias to use

        Returns:
            Redis connection or None if unavailable
        """
        for attempt in range(self._max_retry_attempts):
            try:
                connection = get_redis_connection(alias)

                try:
                    connection.ping()
                except Exception as ping_error:
                    logger.warning(
                        f"Redis ping failed on attempt {attempt + 1}: {ping_error}"
                    )
                    if "Connection closed by server" in str(ping_error):

                        connection.connection_pool.disconnect()
                        if attempt < self._max_retry_attempts - 1:
                            time.sleep(self._retry_delay * (attempt + 1))
                            continue
                        else:
                            raise ping_error

                if not self._connection_healthy and attempt == 0:
                    time.sleep(self._retry_delay)
                    continue

                if self._should_check_health():
                    if self._perform_health_check(connection):
                        self._retry_attempts = 0
                        return connection
                    else:
                        if attempt < self._max_retry_attempts - 1:
                            time.sleep(self._retry_delay * (attempt + 1))
                            continue
                else:
                    return connection

            except Exception as e:
                logger.warning(
                    f"Redis connection attempt {attempt + 1}/{self._max_retry_attempts} failed: {e}"
                )
                self._handle_connection_error()

                if "Connection closed by server" in str(e):
                    logger.warning(
                        "Detected 'Connection closed by server' error, forcing connection pool reset"
                    )
                    try:
                        connection = get_redis_connection(alias)
                        connection.connection_pool.disconnect()
                    except:
                        pass

                if attempt < self._max_retry_attempts - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
                    continue

        logger.error(f"All {self._max_retry_attempts} Redis connection attempts failed")
        return None

    def _should_check_health(self) -> bool:
        """Check if we should perform a health check."""
        current_time = time.time()
        return (current_time - self._last_health_check) > self._health_check_interval

    def _perform_health_check(self, connection: redis.Redis) -> bool:
        """
        Perform a health check on the Redis connection.

        Args:
            connection: Redis connection to check

        Returns:
            True if healthy, False otherwise
        """
        try:

            connection.ping()

            test_key = "health_check_test"
            test_value = "test_value"
            connection.set(test_key, test_value, ex=1)
            retrieved_value = connection.get(test_key)
            connection.delete(test_key)

            if isinstance(retrieved_value, bytes):
                retrieved_value = retrieved_value.decode("utf-8")

            if retrieved_value == test_value:
                self._connection_healthy = True
                self._connection_errors = 0
                self._last_health_check = time.time()
                logger.debug("Redis health check passed")
                return True
            else:
                logger.warning(
                    f"Health check value mismatch: expected '{test_value}', got '{retrieved_value}'"
                )
                raise RedisError(
                    f"Health check value mismatch: expected '{test_value}', got '{retrieved_value}'"
                )

        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            self._handle_connection_error()
            return False

    def _handle_connection_error(self):
        """Handle connection errors with backoff strategy."""
        self._connection_errors += 1
        self._last_health_check = time.time()

        if self._connection_errors > self._max_connection_errors:
            self._connection_healthy = False
            logger.error(
                f"Redis marked as unhealthy after {self._connection_errors} errors"
            )
        else:
            logger.warning(
                f"Redis connection error {self._connection_errors}/{self._max_connection_errors}"
            )

    def is_healthy(self) -> bool:
        """Check if Redis connection is healthy."""
        return self._connection_healthy

    def reset_health_status(self):
        """Reset health status (useful for recovery)."""
        self._connection_healthy = True
        self._connection_errors = 0
        self._last_health_check = 0
        logger.info("Redis health status reset")


redis_manager = RedisConnectionManager()


def redis_safe(fallback_value=None, log_errors=True):
    """
    Decorator for Redis operations that provides graceful fallback.

    Args:
        fallback_value: Value to return if Redis is unavailable
        log_errors: Whether to log errors
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (ConnectionError, TimeoutError, RedisError) as e:
                if log_errors:
                    logger.warning(f"Redis operation failed in {func.__name__}: {e}")
                redis_manager._handle_connection_error()
                return fallback_value
            except Exception as e:
                if log_errors:
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                return fallback_value

        return wrapper

    return decorator


class SafeCache:
    """
    A safe cache wrapper that handles Redis connection failures gracefully.
    """

    def __init__(self, cache_alias: str = "default"):
        self.cache_alias = cache_alias
        self.cache = cache

    @redis_safe(fallback_value=None)
    def get(self, key: str, default=None, version=None) -> Any:
        """Safe cache get with fallback."""
        return self.cache.get(key, default, version)

    @redis_safe(fallback_value=False)
    def set(self, key: str, value: Any, timeout=None, version=None) -> bool:
        """Safe cache set with fallback."""
        return self.cache.set(key, value, timeout, version)

    @redis_safe(fallback_value=False)
    def delete(self, key: str, version=None) -> bool:
        """Safe cache delete with fallback."""
        return self.cache.delete(key, version)

    @redis_safe(fallback_value={})
    def get_many(self, keys: List[str], version=None) -> Dict[str, Any]:
        """Safe cache get_many with fallback."""
        return self.cache.get_many(keys, version)

    @redis_safe(fallback_value=False)
    def set_many(self, data: Dict[str, Any], timeout=None, version=None) -> bool:
        """Safe cache set_many with fallback."""
        return self.cache.set_many(data, timeout, version)

    @redis_safe(fallback_value=False)
    def delete_many(self, keys: List[str], version=None) -> bool:
        """Safe cache delete_many with fallback."""
        return self.cache.delete_many(keys, version)

    def clear(self) -> bool:
        """
        Safe cache clear with enhanced error handling and retry logic.

        Returns:
            True if cache was cleared successfully, False otherwise
        """
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                logger.info(f"Cache clear attempt {attempt + 1}/{max_attempts}")

                result = self.cache.clear()
                if result:
                    logger.info("Cache cleared successfully via direct method")
                    return True

                connection = redis_manager.get_connection()
                if connection:
                    try:

                        if attempt > 0:
                            connection.connection_pool.disconnect()
                            connection = redis_manager.get_connection()

                        if connection:
                            connection.flushdb()
                            logger.info("Cache cleared successfully via Redis FLUSHDB")
                            return True
                    except Exception as e:
                        logger.warning(f"Redis FLUSHDB failed: {e}")

                        if "Connection closed by server" in str(e):
                            logger.warning(
                                "Retrying cache clear after connection reset..."
                            )
                            if attempt < max_attempts - 1:
                                time.sleep(2 * (attempt + 1))
                                continue

                        try:
                            if connection:
                                keys = connection.keys("*")
                                if keys:

                                    batch_size = 100
                                    for i in range(0, len(keys), batch_size):
                                        batch = keys[i : i + batch_size]
                                        connection.delete(*batch)
                                    logger.info(
                                        f"Cache cleared successfully via key deletion ({len(keys)} keys)"
                                    )
                                    return True
                                else:
                                    logger.info("No cache keys found to clear")
                                    return True
                        except Exception as pattern_e:
                            logger.warning(
                                f"Pattern-based cache clear failed: {pattern_e}"
                            )

                if attempt < max_attempts - 1:
                    logger.warning(
                        f"Cache clear attempt {attempt + 1} failed, retrying..."
                    )
                    time.sleep(2 * (attempt + 1))

            except Exception as e:
                logger.error(
                    f"Cache clear operation failed on attempt {attempt + 1}: {e}"
                )
                if attempt < max_attempts - 1:
                    time.sleep(2 * (attempt + 1))
                    continue

        logger.warning("All cache clear methods failed")
        return False


class CacheInvalidationManager:
    """
    Manages cache invalidation strategies for different model types.
    """

    def __init__(self):
        self.safe_cache = SafeCache()
        self.invalidation_patterns = {
            "user": ["user_*", "profile_*", "auth_*"],
            "post": ["post_*", "feed_*", "social_*"],
            "stats": ["stats_*", "analytics_*", "dashboard_*"],
            "payment": ["payment_*", "transaction_*", "wallet_*"],
            "card": ["card_*", "deck_*", "collection_*"],
        }

    def invalidate_model_cache(
        self, model_type: str, instance_id: Optional[int] = None
    ):
        """
        Invalidate cache for a specific model type.

        Args:
            model_type: Type of model (user, post, stats, etc.)
            instance_id: Specific instance ID to invalidate
        """
        patterns = self.invalidation_patterns.get(model_type, [])

        for pattern in patterns:
            if instance_id:

                specific_keys = [
                    f"{pattern.replace('*', str(instance_id))}",
                    f"{pattern.replace('*', f'{instance_id}_*')}",
                ]
                for key in specific_keys:
                    self.safe_cache.delete(key)
            else:

                self._invalidate_pattern(pattern)

    def _invalidate_pattern(self, pattern: str):
        """
        Invalidate all cache keys matching a pattern.

        Args:
            pattern: Cache key pattern to match
        """
        try:

            if hasattr(cache, "_cache") and hasattr(cache._cache, "_cache"):

                connection = redis_manager.get_connection()
                if connection:
                    keys = connection.keys(pattern)
                    if keys:
                        connection.delete(*keys)
                        logger.info(
                            f"Invalidated {len(keys)} cache keys for pattern: {pattern}"
                        )
            else:

                if hasattr(cache, "_cache"):

                    cache_backend = cache._cache
                    keys_to_delete = []

                    pattern_prefix = pattern.replace("*", "")

                    if hasattr(cache_backend, "_data"):

                        cache_data = cache_backend._data
                    elif isinstance(cache_backend, dict):

                        cache_data = cache_backend
                    else:

                        cache_data = {}
                        for i in range(1000):
                            test_key = f"test_key_{i}"
                            if cache.get(test_key) is not None:
                                cache_data[test_key] = True

                    for key in cache_data.keys():

                        cache_key_without_prefix = (
                            key.split(":", 2)[-1] if ":" in key else key
                        )
                        if cache_key_without_prefix.startswith(pattern_prefix):
                            keys_to_delete.append(key)

                    for key in keys_to_delete:

                        cache_key_without_prefix = (
                            key.split(":", 2)[-1] if ":" in key else key
                        )
                        cache.delete(cache_key_without_prefix)

                        if isinstance(cache_backend, dict) and key in cache_backend:
                            del cache_backend[key]

                    if keys_to_delete:
                        logger.info(
                            f"Invalidated {len(keys_to_delete)} cache keys for pattern: {pattern}"
                        )
        except Exception as e:
            logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")

    def invalidate_user_cache(self, user_id: int):
        """Invalidate all caches related to a user."""
        self._invalidate_pattern(f"user_{user_id}_*")

    def invalidate_post_cache(self, post_id: int):
        """Invalidate all caches related to a post."""
        self.invalidate_model_cache("post", post_id)

    def invalidate_stats_cache(self):
        """Invalidate all stats-related caches."""
        self._invalidate_pattern("stats_*")

    def invalidate_dashboard_cache(self, user_id: Optional[int] = None):
        """Invalidate dashboard caches."""
        if user_id:
            patterns = [f"dashboard_{user_id}_*", f"user_{user_id}_dashboard_*"]
            for pattern in patterns:
                self._invalidate_pattern(pattern)
        else:
            self._invalidate_pattern("dashboard_*")


cache_invalidation_manager = CacheInvalidationManager()


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a consistent cache key.

    Args:
        prefix: Cache key prefix
        *args: Additional arguments for the key
        **kwargs: Additional keyword arguments for the key

    Returns:
        Generated cache key
    """
    key_parts = [prefix]

    for arg in args:
        key_parts.append(str(arg))

    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}_{value}")

    return "_".join(key_parts)


def cached_method(timeout: int = 300, key_prefix: str = "method"):
    """
    Decorator for caching method results that respects ENABLE_CACHE setting.

    Args:
        timeout: Cache timeout in seconds
        key_prefix: Cache key prefix
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):

            from django.conf import settings

            if not getattr(settings, "ENABLE_CACHE", True):
                logger.debug(
                    f"Cache disabled - executing {func.__name__} without caching"
                )
                return func(self, *args, **kwargs)

            cache_key = get_cache_key(
                key_prefix, func.__name__, getattr(self, "id", ""), *args, **kwargs
            )

            safe_cache = SafeCache()
            cached_result = safe_cache.get(cache_key)

            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            result = func(self, *args, **kwargs)
            safe_cache.set(cache_key, result, timeout)
            logger.debug(f"Cache set for {cache_key}")

            return result

        return wrapper

    return decorator


class CacheMonitor:
    """
    Monitors cache performance and health.
    """

    def __init__(self):
        self.stats = {"hits": 0, "misses": 0, "errors": 0, "last_reset": time.time()}

    def record_hit(self):
        """Record a cache hit."""
        self.stats["hits"] += 1

    def record_miss(self):
        """Record a cache miss."""
        self.stats["misses"] += 1

    def record_error(self):
        """Record a cache error."""
        self.stats["errors"] += 1

    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self.stats["hits"] + self.stats["misses"]
        return (self.stats["hits"] / total) if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return {
            **self.stats,
            "hit_rate": self.get_hit_rate(),
            "redis_healthy": redis_manager.is_healthy(),
            "uptime": time.time() - self.stats["last_reset"],
        }

    def reset_stats(self):
        """Reset cache statistics."""
        self.stats = {"hits": 0, "misses": 0, "errors": 0, "last_reset": time.time()}


cache_monitor = CacheMonitor()
