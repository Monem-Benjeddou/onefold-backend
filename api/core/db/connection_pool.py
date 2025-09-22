"""
Database connection pool manager for optimized connection handling.
"""

import threading
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any
from django.db import connections, connection
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """
    Manages database connections with pooling for high concurrency.
    """

    _local = threading.local()
    _pool_stats = {
        "connections_created": 0,
        "connections_reused": 0,
        "connections_closed": 0,
        "active_connections": 0,
        "errors": 0,
    }

    @classmethod
    def get_pool_settings(cls) -> Dict[str, Any]:
        """Get connection pool settings from Django settings."""
        return getattr(
            settings,
            "DATABASE_CONNECTION_POOLING",
            {
                "POOL_SIZE": 20,
                "MAX_OVERFLOW": 10,
                "POOL_TIMEOUT": 30,
                "POOL_RECYCLE": 3600,
                "POOL_PRE_PING": True,
            },
        )

    @classmethod
    @contextmanager
    def get_connection(cls, using: str = "default", readonly: bool = False):
        """
        Get a database connection from the pool.

        Args:
            using: Database alias to use
            readonly: If True, use read-only connection settings

        Yields:
            Database connection
        """
        conn = None
        pool_settings = cls.get_pool_settings()

        try:

            conn = connections[using]

            if pool_settings.get("POOL_PRE_PING", True):
                cls._test_connection(conn)

            cls._pool_stats["active_connections"] += 1
            if not hasattr(cls._local, "connection_count"):
                cls._local.connection_count = 0
                cls._pool_stats["connections_created"] += 1
            else:
                cls._pool_stats["connections_reused"] += 1

            cls._local.connection_count += 1

            if readonly and hasattr(conn, "cursor"):
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY"
                    )

            yield conn

        except Exception as e:
            cls._pool_stats["errors"] += 1
            logger.error(f"Connection pool error: {e}")
            raise

        finally:
            cls._pool_stats["active_connections"] -= 1

            if conn and hasattr(conn, "close_if_unusable_or_obsolete"):
                conn.close_if_unusable_or_obsolete()

    @classmethod
    def _test_connection(cls, conn):
        """Test if connection is still alive."""
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:

            if hasattr(conn, "close"):
                conn.close()
            raise

    @classmethod
    def close_old_connections(cls):
        """Close connections older than CONN_MAX_AGE."""
        for conn in connections.all():
            conn.close_if_unusable_or_obsolete()
        cls._pool_stats["connections_closed"] += 1

    @classmethod
    def get_pool_stats(cls) -> Dict[str, Any]:
        """Get current pool statistics."""
        return cls._pool_stats.copy()

    @classmethod
    def reset_pool_stats(cls):
        """Reset pool statistics."""
        cls._pool_stats = {
            "connections_created": 0,
            "connections_reused": 0,
            "connections_closed": 0,
            "active_connections": 0,
            "errors": 0,
        }


class ConnectionMiddleware:
    """
    Middleware to manage database connections per request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        DatabaseConnectionPool.close_old_connections()

        response = self.get_response(request)

        DatabaseConnectionPool.close_old_connections()

        return response


def execute_in_chunks(queryset, chunk_size: int = 1000, callback=None):
    """
    Execute database operations in chunks to avoid connection overload.

    Args:
        queryset: Django queryset to process
        chunk_size: Number of items per chunk
        callback: Function to call for each chunk
    """
    total = queryset.count()

    for offset in range(0, total, chunk_size):
        chunk = queryset[offset : offset + chunk_size]

        with DatabaseConnectionPool.get_connection() as conn:
            if callback:
                callback(chunk)
            else:

                list(chunk)

        DatabaseConnectionPool.close_old_connections()


def get_database_connection_info():
    """
    Get current database connection information.

    Returns:
        Dictionary with connection statistics
    """
    info = {
        "pool_stats": DatabaseConnectionPool.get_pool_stats(),
        "django_connections": {},
        "database_info": {},
    }

    for alias in connections:
        conn = connections[alias]
        try:
            is_usable = conn.is_usable() if hasattr(conn, "is_usable") else "unknown"
        except Exception:
            is_usable = "error"

        info["django_connections"][alias] = {
            "vendor": getattr(conn, "vendor", "unknown"),
            "queries_count": len(conn.queries) if settings.DEBUG else "N/A",
            "is_usable": is_usable,
        }

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active,
                    count(*) FILTER (WHERE state = 'idle') as idle,
                    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_trans,
                    max(now() - query_start) FILTER (WHERE state = 'active') as longest_query_time
                FROM pg_stat_activity
                WHERE datname = current_database()
            """
            )
            row = cursor.fetchone()
            info["database_info"] = {
                "total_connections": row[0],
                "active_connections": row[1],
                "idle_connections": row[2],
                "idle_in_transaction": row[3],
                "longest_query_time": str(row[4]) if row[4] else None,
            }
    except Exception as e:
        info["database_info"]["error"] = str(e)

    return info
