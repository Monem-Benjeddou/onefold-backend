"""
Cache utilities that respect the ENABLE_CACHE setting.

This module provides utility functions and classes for cache operations
that automatically respect the global ENABLE_CACHE setting. When caching
is disabled, all operations become no-ops.
"""

from typing import Any, Optional, Union, List, Dict
import logging
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


def is_cache_enabled() -> bool:
    """
    Check if caching is enabled globally.

    Returns:
        bool: True if caching is enabled, False otherwise
    """
    return getattr(settings, "ENABLE_CACHE", True)


class CacheManager:
    """
    A cache manager that respects the ENABLE_CACHE setting.

    This class provides a unified interface for cache operations that
    automatically handles the case when caching is disabled globally.
    """

    def __init__(self, cache_alias: str = "default"):
        """
        Initialize the cache manager.

        Args:
            cache_alias: Cache alias to use
        """
        self.cache_alias = cache_alias
        self.cache = cache

    def get(self, key: str, default: Any = None, version: Optional[int] = None) -> Any:
        """
        Get value from cache if caching is enabled.

        Args:
            key: Cache key
            default: Default value if key not found
            version: Cache version

        Returns:
            Cached value or default if caching disabled/key not found
        """
        if not is_cache_enabled():
            logger.debug(f"Cache disabled - returning default for key: {key}")
            return default

        try:
            result = self.cache.get(key, default, version)
            if result != default:
                logger.debug(f"Cache hit for key: {key}")
            else:
                logger.debug(f"Cache miss for key: {key}")
            return result
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return default

    def set(
        self,
        key: str,
        value: Any,
        timeout: Optional[int] = None,
        version: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache if caching is enabled.

        Args:
            key: Cache key
            value: Value to cache
            timeout: Cache timeout in seconds
            version: Cache version

        Returns:
            True if value was set, False if caching disabled or failed
        """
        if not is_cache_enabled():
            logger.debug(f"Cache disabled - skipping set for key: {key}")
            return False

        try:
            result = self.cache.set(key, value, timeout, version)
            logger.debug(f"Cache set for key: {key}")
            return result
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False

    def delete(self, key: str, version: Optional[int] = None) -> bool:
        """
        Delete value from cache if caching is enabled.

        Args:
            key: Cache key
            version: Cache version

        Returns:
            True if key was deleted, False if caching disabled or failed
        """
        if not is_cache_enabled():
            logger.debug(f"Cache disabled - skipping delete for key: {key}")
            return False

        try:
            result = self.cache.delete(key, version)
            logger.debug(f"Cache delete for key: {key}")
            return result
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return False

    def get_many(
        self, keys: List[str], version: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get multiple values from cache if caching is enabled.

        Args:
            keys: List of cache keys
            version: Cache version

        Returns:
            Dictionary of key-value pairs, empty if caching disabled
        """
        if not is_cache_enabled():
            logger.debug(f"Cache disabled - returning empty dict for keys: {keys}")
            return {}

        try:
            result = self.cache.get_many(keys, version)
            logger.debug(f"Cache get_many for {len(keys)} keys, {len(result)} hits")
            return result
        except Exception as e:
            logger.warning(f"Cache get_many failed for keys {keys}: {e}")
            return {}

    def set_many(
        self,
        data: Dict[str, Any],
        timeout: Optional[int] = None,
        version: Optional[int] = None,
    ) -> List[str]:
        """
        Set multiple values in cache if caching is enabled.

        Args:
            data: Dictionary of key-value pairs to cache
            timeout: Cache timeout in seconds
            version: Cache version

        Returns:
            List of keys that failed to be set
        """
        if not is_cache_enabled():
            logger.debug(f"Cache disabled - skipping set_many for {len(data)} keys")
            return list(data.keys())

        try:
            result = self.cache.set_many(data, timeout, version)
            logger.debug(f"Cache set_many for {len(data)} keys")
            return result
        except Exception as e:
            logger.warning(f"Cache set_many failed: {e}")
            return list(data.keys())

    def delete_many(self, keys: List[str], version: Optional[int] = None) -> None:
        """
        Delete multiple values from cache if caching is enabled.

        Args:
            keys: List of cache keys to delete
            version: Cache version
        """
        if not is_cache_enabled():
            logger.debug(f"Cache disabled - skipping delete_many for keys: {keys}")
            return

        try:
            self.cache.delete_many(keys, version)
            logger.debug(f"Cache delete_many for {len(keys)} keys")
        except Exception as e:
            logger.warning(f"Cache delete_many failed for keys {keys}: {e}")

    def clear(self) -> bool:
        """
        Clear all cache if caching is enabled.

        Returns:
            True if cache was cleared, False if caching disabled or failed
        """
        if not is_cache_enabled():
            logger.debug("Cache disabled - skipping clear")
            return False

        try:
            self.cache.clear()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")
            return False

    def touch(
        self, key: str, timeout: Optional[int] = None, version: Optional[int] = None
    ) -> bool:
        """
        Touch cache key to update its timeout if caching is enabled.

        Args:
            key: Cache key
            timeout: New timeout in seconds
            version: Cache version

        Returns:
            True if key was touched, False if caching disabled or failed
        """
        if not is_cache_enabled():
            logger.debug(f"Cache disabled - skipping touch for key: {key}")
            return False

        try:
            result = self.cache.touch(key, timeout, version)
            logger.debug(f"Cache touch for key: {key}")
            return result
        except Exception as e:
            logger.warning(f"Cache touch failed for key {key}: {e}")
            return False

    def incr(
        self, key: str, delta: int = 1, version: Optional[int] = None
    ) -> Optional[int]:
        """
        Increment cache value if caching is enabled.

        Args:
            key: Cache key
            delta: Increment amount
            version: Cache version

        Returns:
            New value after increment, None if caching disabled or failed
        """
        if not is_cache_enabled():
            logger.debug(f"Cache disabled - skipping incr for key: {key}")
            return None

        try:
            result = self.cache.incr(key, delta, version)
            logger.debug(f"Cache incr for key: {key}, new value: {result}")
            return result
        except Exception as e:
            logger.warning(f"Cache incr failed for key {key}: {e}")
            return None

    def decr(
        self, key: str, delta: int = 1, version: Optional[int] = None
    ) -> Optional[int]:
        """
        Decrement cache value if caching is enabled.

        Args:
            key: Cache key
            delta: Decrement amount
            version: Cache version

        Returns:
            New value after decrement, None if caching disabled or failed
        """
        if not is_cache_enabled():
            logger.debug(f"Cache disabled - skipping decr for key: {key}")
            return None

        try:
            result = self.cache.decr(key, delta, version)
            logger.debug(f"Cache decr for key: {key}, new value: {result}")
            return result
        except Exception as e:
            logger.warning(f"Cache decr failed for key {key}: {e}")
            return None


cache_manager = CacheManager()


def get_cache_key(*parts: Union[str, int]) -> str:
    """
    Generate a cache key from multiple parts.

    Args:
        *parts: Parts to join into cache key

    Returns:
        str: Generated cache key
    """
    return ":".join(str(part) for part in parts if part is not None)


def cache_get_or_set(
    key: str, default_func: callable, timeout: Optional[int] = None
) -> Any:
    """
    Get value from cache or set it using default function if caching is enabled.

    Args:
        key: Cache key
        default_func: Function to call if key not in cache
        timeout: Cache timeout in seconds

    Returns:
        Cached value or result of default_func
    """
    if not is_cache_enabled():
        logger.debug(f"Cache disabled - executing default function for key: {key}")
        return default_func()

    try:
        cached_value = cache_manager.get(key)
        if cached_value is not None:
            return cached_value

        value = default_func()
        cache_manager.set(key, value, timeout)
        return value
    except Exception as e:
        logger.warning(f"Cache get_or_set failed for key {key}: {e}")
        return default_func()


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate cache keys matching a pattern if caching is enabled.

    Args:
        pattern: Pattern to match (supports wildcards)

    Returns:
        Number of keys invalidated, 0 if caching disabled
    """
    if not is_cache_enabled():
        logger.debug(f"Cache disabled - skipping pattern invalidation: {pattern}")
        return 0

    try:
        from django_redis import get_redis_connection

        redis_conn = get_redis_connection("default")

        keys = redis_conn.keys(pattern)
        if keys:
            redis_conn.delete(*keys)
            logger.info(
                f"Invalidated {len(keys)} cache keys matching pattern: {pattern}"
            )
            return len(keys)

        return 0
    except Exception as e:
        logger.warning(f"Cache pattern invalidation failed for pattern {pattern}: {e}")
        return 0
