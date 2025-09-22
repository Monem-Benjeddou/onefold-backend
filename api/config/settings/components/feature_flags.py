"""
Feature flags and configuration settings for the Kolct application.

This module provides centralized access to feature flags and configuration
options that can be toggled or adjusted based on environment or runtime conditions.
"""

from django.conf import settings


class FeatureFlags:
    """
    Centralized feature flag management for the application.
    """

    @classmethod
    def get_timeout_multiplier(cls) -> float:
        """
        Get the Celery timeout multiplier setting.

        This multiplier is applied to all task timeout values to allow
        for environmental adjustments (e.g., slower development environments).

        Returns:
            float: Multiplier value (default: 1.0)
        """
        multiplier = getattr(settings, "CELERY_TIMEOUT_MULTIPLIER", 1.0)

        if multiplier < 1.0:
            multiplier = 1.0
        elif multiplier > 10.0:
            multiplier = 10.0

        return float(multiplier)

    @classmethod
    def is_timeout_enabled(cls) -> bool:
        """
        Check if Celery task timeouts are enabled.

        Returns:
            bool: True if timeouts are enabled
        """
        return getattr(settings, "CELERY_TASK_TIMEOUTS_ENABLED", False)

    @classmethod
    def is_timeout_monitoring_enabled(cls) -> bool:
        """
        Check if timeout monitoring is enabled.

        Returns:
            bool: True if timeout monitoring is enabled
        """
        return getattr(settings, "CELERY_TIMEOUT_MONITORING_ENABLED", False)

    @classmethod
    def get_bulk_card_creation_batch_size(cls) -> int:
        """
        Get the batch size for bulk card creation operations.

        Returns:
            int: Batch size (default: 100)
        """
        return getattr(settings, "BULK_CARD_CREATION_BATCH_SIZE", 100)

    @classmethod
    def get_cart_cleanup_max_items(cls) -> int:
        """
        Get the maximum items to process in cart cleanup operations.

        Returns:
            int: Maximum items (default: 1000)
        """
        return getattr(settings, "CART_CLEANUP_MAX_ITEMS", 1000)

    @classmethod
    def get_orphaned_cart_cleanup_batch_size(cls) -> int:
        """
        Get the batch size for orphaned cart cleanup operations.

        Returns:
            int: Batch size (default: 500)
        """
        return getattr(settings, "ORPHANED_CART_CLEANUP_BATCH_SIZE", 500)

    @classmethod
    def get_stats_generation_max_items(cls) -> int:
        """
        Get the maximum items to process in stats generation operations.

        Returns:
            int: Maximum items (default: 100)
        """
        return getattr(settings, "STATS_GENERATION_MAX_ITEMS", 100)
