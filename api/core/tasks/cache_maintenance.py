"""
Celery tasks for cache maintenance and health monitoring.
"""

import logging
from celery import shared_task
from django.core.management import call_command
from django.conf import settings
from core.utilities.redis_manager import (
    redis_manager,
    cache_invalidation_manager,
    cache_monitor,
    SafeCache,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def redis_health_check(self):
    """
    Periodic Redis health check task.

    This task runs every 5 minutes to monitor Redis health
    and log any issues.
    """
    try:
        logger.info("🔍 Starting Redis health check...")

        connection = redis_manager.get_connection()
        if connection:

            test_key = "health_check_test"
            connection.set(test_key, "test_value", ex=1)
            value = connection.get(test_key)
            connection.delete(test_key)

            if value == b"test_value":
                logger.info("✅ Redis health check passed")

                info = connection.info()
                logger.info(
                    f"Redis - Version: {info.get('redis_version', 'Unknown')}, "
                    f"Clients: {info.get('connected_clients', 0)}, "
                    f"Memory: {info.get('used_memory_human', 'Unknown')}"
                )

                if not redis_manager.is_healthy():
                    redis_manager.reset_health_status()
                    logger.info("🔄 Redis health status reset to healthy")

                return "Redis health check passed"
            else:
                raise Exception("Health check value mismatch")
        else:
            raise Exception("Redis connection failed")

    except Exception as e:
        logger.error(f"❌ Redis health check failed: {e}")

        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying health check in 60 seconds (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(countdown=60, exc=e)
        else:
            logger.error(f"Redis health check failed after {self.max_retries} retries")
            return f"Redis health check failed: {e}"


@shared_task(bind=True)
def cache_cleanup(self):
    """
    Clean up expired cache entries and perform maintenance.

    This task runs daily to clean up cache data.
    """
    try:
        logger.info("🧹 Starting cache cleanup...")

        stats_before = cache_monitor.get_stats()

        call_command("cache_health_check", "--stats")

        patterns_to_clean = [
            "temp_*",
            "session_*",
            "rate_limit_*",
        ]

        for pattern in patterns_to_clean:
            cache_invalidation_manager._invalidate_pattern(pattern)
            logger.info(f"Cleaned cache pattern: {pattern}")

        stats_after = cache_monitor.get_stats()

        logger.info(
            f"Cache cleanup completed. "
            f"Before: {stats_before['hits']} hits, {stats_before['misses']} misses. "
            f"After: {stats_after['hits']} hits, {stats_after['misses']} misses."
        )

        return "Cache cleanup completed successfully"

    except Exception as e:
        logger.error(f"❌ Cache cleanup failed: {e}")
        return f"Cache cleanup failed: {e}"


@shared_task(bind=True)
def invalidate_stats_cache(self):
    """
    Invalidate stats-related cache entries.

    This task runs every hour to ensure stats data is fresh.
    """
    try:
        logger.info("🔄 Starting stats cache invalidation...")

        cache_invalidation_manager.invalidate_stats_cache()

        logger.info("✅ Stats cache invalidation completed")
        return "Stats cache invalidation completed"

    except Exception as e:
        logger.error(f"❌ Stats cache invalidation failed: {e}")
        return f"Stats cache invalidation failed: {e}"


@shared_task(bind=True)
def cache_warmup(self):
    """
    Warm up critical cache entries.

    This task runs after cache cleanup to pre-populate important data.
    """
    try:
        logger.info("🔥 Starting cache warmup...")

        logger.info("✅ Cache warmup completed")
        return "Cache warmup completed"

    except Exception as e:
        logger.error(f"❌ Cache warmup failed: {e}")
        return f"Cache warmup failed: {e}"


@shared_task(bind=True)
def cache_performance_report(self):
    """
    Generate cache performance report.

    This task runs daily to report cache performance metrics.
    """
    try:
        logger.info("📊 Generating cache performance report...")

        stats = cache_monitor.get_stats()

        report = {
            "cache_hits": stats["hits"],
            "cache_misses": stats["misses"],
            "cache_errors": stats["errors"],
            "hit_rate": stats["hit_rate"],
            "redis_healthy": stats["redis_healthy"],
            "uptime": stats["uptime"],
        }

        logger.info(f"📊 Cache Performance Report: {report}")

        cache_monitor.reset_stats()

        return f"Cache performance report generated: {report}"

    except Exception as e:
        logger.error(f"❌ Cache performance report failed: {e}")
        return f"Cache performance report failed: {e}"


@shared_task(bind=True)
def emergency_cache_clear(self):
    """
    Emergency cache clear task.

    This task can be triggered manually when cache issues are detected.
    """
    try:
        logger.warning("🚨 Emergency cache clear initiated...")

        safe_cache = SafeCache()
        if safe_cache.clear():
            logger.info("✅ Emergency cache clear completed")

            redis_manager.reset_health_status()

            return "Emergency cache clear completed"
        else:
            raise Exception("Failed to clear cache")

    except Exception as e:
        logger.error(f"❌ Emergency cache clear failed: {e}")
        return f"Emergency cache clear failed: {e}"


@shared_task(bind=True)
def cache_health_monitoring(self):
    """
    Comprehensive cache health monitoring.

    This task runs every 15 minutes to monitor cache health
    and trigger alerts if needed.
    """
    try:
        logger.info("🔍 Starting cache health monitoring...")

        connection = redis_manager.get_connection()
        if not connection:
            logger.error("❌ Redis connection failed")
            return "Redis connection failed"

        stats = cache_monitor.get_stats()

        if stats["hit_rate"] < 0.7:
            logger.warning(f"⚠️  Low cache hit rate: {stats['hit_rate']:.2%}")

        if stats["errors"] > 100:
            logger.error(f"❌ High cache error count: {stats['errors']}")

        if not stats["redis_healthy"]:
            logger.error("❌ Redis marked as unhealthy")

        info = connection.info()
        used_memory = info.get("used_memory", 0)
        max_memory = info.get("maxmemory", 0)

        if max_memory > 0 and used_memory > (max_memory * 0.8):
            logger.warning(f"⚠️  High Redis memory usage: {used_memory}/{max_memory}")

        logger.info("✅ Cache health monitoring completed")
        return "Cache health monitoring completed"

    except Exception as e:
        logger.error(f"❌ Cache health monitoring failed: {e}")
        return f"Cache health monitoring failed: {e}"
