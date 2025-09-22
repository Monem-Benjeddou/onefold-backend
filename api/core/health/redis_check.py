"""
Redis Health Check Module

Provides utilities for monitoring Redis connection health and performance.
"""

import logging
import time
from typing import Dict, Any, Optional
from django.core.cache import cache, caches
from django.conf import settings
from django_redis import get_redis_connection
from redis.exceptions import ConnectionError, TimeoutError, AuthenticationError

logger = logging.getLogger(__name__)


class RedisHealthChecker:
    """
    Redis health checker with comprehensive monitoring capabilities.
    """

    def __init__(self):
        self.last_check_time = 0
        self.check_interval = 30
        self.consecutive_failures = 0
        self.max_failures_before_alert = 3

    def check_redis_health(self, cache_alias: str = "default") -> Dict[str, Any]:
        """
        Perform comprehensive Redis health check.

        Args:
            cache_alias: The cache alias to check

        Returns:
            Dict containing health status and metrics
        """
        start_time = time.time()
        health_status = {
            "status": "unknown",
            "cache_alias": cache_alias,
            "timestamp": start_time,
            "response_time_ms": 0,
            "error": None,
            "connection_info": {},
            "metrics": {},
        }

        try:

            redis_conn = get_redis_connection(cache_alias)

            ping_start = time.time()
            ping_result = redis_conn.ping()
            ping_time = (time.time() - ping_start) * 1000

            if not ping_result:
                raise ConnectionError("Redis ping returned False")

            test_key = f"health_check_{int(start_time)}"
            test_value = "health_check_value"

            set_start = time.time()
            cache.set(test_key, test_value, timeout=10)
            set_time = (time.time() - set_start) * 1000

            get_start = time.time()
            retrieved_value = cache.get(test_key)
            get_time = (time.time() - get_start) * 1000

            if retrieved_value != test_value:
                raise ValueError("Set/Get test failed - values don't match")

            cache.delete(test_key)

            info = redis_conn.info()

            health_status.update(
                {
                    "status": "healthy",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "metrics": {
                        "ping_time_ms": round(ping_time, 2),
                        "set_time_ms": round(set_time, 2),
                        "get_time_ms": round(get_time, 2),
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory": info.get("used_memory", 0),
                        "used_memory_human": info.get("used_memory_human", "0B"),
                        "keyspace_hits": info.get("keyspace_hits", 0),
                        "keyspace_misses": info.get("keyspace_misses", 0),
                        "total_commands_processed": info.get(
                            "total_commands_processed", 0
                        ),
                    },
                    "connection_info": {
                        "redis_version": info.get("redis_version", "unknown"),
                        "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                        "role": info.get("role", "unknown"),
                    },
                }
            )

            self.consecutive_failures = 0

            logger.debug(f"Redis health check passed for {cache_alias}")

        except (ConnectionError, TimeoutError, AuthenticationError) as e:
            self.consecutive_failures += 1
            health_status.update(
                {
                    "status": "unhealthy",
                    "error": f"{type(e).__name__}: {str(e)}",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "consecutive_failures": self.consecutive_failures,
                }
            )

            if self.consecutive_failures >= self.max_failures_before_alert:
                logger.error(
                    f"Redis health check failed {self.consecutive_failures} times "
                    f"for {cache_alias}: {e}"
                )
            else:
                logger.warning(f"Redis health check failed for {cache_alias}: {e}")

        except Exception as e:
            self.consecutive_failures += 1
            health_status.update(
                {
                    "status": "error",
                    "error": f"Unexpected error: {type(e).__name__}: {str(e)}",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "consecutive_failures": self.consecutive_failures,
                }
            )

            logger.error(
                f"Unexpected error in Redis health check for {cache_alias}: {e}"
            )

        self.last_check_time = start_time
        return health_status

    def check_all_caches(self) -> Dict[str, Dict[str, Any]]:
        """
        Check health of all configured Redis caches.

        Returns:
            Dict mapping cache aliases to their health status
        """
        results = {}

        cache_configs = getattr(settings, "CACHES", {})

        for alias, config in cache_configs.items():

            if "redis" in config.get("BACKEND", "").lower():
                results[alias] = self.check_redis_health(alias)
            else:
                results[alias] = {
                    "status": "skipped",
                    "reason": f"Non-Redis backend: {config.get('BACKEND', 'unknown')}",
                    "timestamp": time.time(),
                }

        return results

    def get_fallback_status(self) -> Dict[str, Any]:
        """
        Check if fallback cache is working properly.

        Returns:
            Dict containing fallback cache status
        """
        try:
            fallback_cache = caches["fallback"]
            test_key = f"fallback_test_{int(time.time())}"
            test_value = "fallback_test_value"

            fallback_cache.set(test_key, test_value, timeout=10)
            retrieved_value = fallback_cache.get(test_key)
            fallback_cache.delete(test_key)

            if retrieved_value == test_value:
                return {
                    "status": "healthy",
                    "backend": "django.core.cache.backends.locmem.LocMemCache",
                    "test_passed": True,
                }
            else:
                return {
                    "status": "unhealthy",
                    "backend": "django.core.cache.backends.locmem.LocMemCache",
                    "test_passed": False,
                    "error": "Set/Get test failed",
                }

        except Exception as e:
            return {
                "status": "error",
                "error": f"{type(e).__name__}: {str(e)}",
                "test_passed": False,
            }


redis_health_checker = RedisHealthChecker()


def get_redis_health_summary() -> Dict[str, Any]:
    """
    Get a comprehensive Redis health summary.

    Returns:
        Dict containing overall Redis health status
    """
    all_caches = redis_health_checker.check_all_caches()
    fallback_status = redis_health_checker.get_fallback_status()

    redis_caches = {k: v for k, v in all_caches.items() if v.get("status") != "skipped"}
    healthy_count = sum(
        1 for status in redis_caches.values() if status.get("status") == "healthy"
    )
    total_redis_caches = len(redis_caches)

    if total_redis_caches == 0:
        overall_status = "no_redis_caches"
    elif healthy_count == total_redis_caches:
        overall_status = "healthy"
    elif healthy_count > 0:
        overall_status = "partially_healthy"
    else:
        overall_status = "unhealthy"

    return {
        "overall_status": overall_status,
        "healthy_caches": healthy_count,
        "total_redis_caches": total_redis_caches,
        "cache_details": all_caches,
        "fallback_cache": fallback_status,
        "timestamp": time.time(),
    }
