"""
Django signals for automatic cache invalidation.

This module provides automatic cache invalidation when models are modified.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from core.utilities.redis_manager import cache_invalidation_manager

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(post_save, sender=User)
@receiver(post_delete, sender=User)
def invalidate_user_cache(sender, instance, **kwargs):
    """
    Invalidate user-related cache when user is modified.

    Args:
        sender: The model class
        instance: The instance being saved/deleted
        **kwargs: Additional keyword arguments
    """
    try:
        user_id = instance.pk
        if user_id:
            cache_invalidation_manager.invalidate_user_cache(user_id)
            logger.info(f"🔄 Invalidated user cache for user ID: {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to invalidate user cache: {e}")


# Stats app not installed - commenting out stats cache signals
# @receiver(post_save, sender="stats.DailyStats")
# @receiver(post_delete, sender="stats.DailyStats")
# @receiver(post_save, sender="stats.UserActivityLog")
# @receiver(post_delete, sender="stats.UserActivityLog")
# @receiver(post_save, sender="stats.GoogleAnalyticsMetrics")
# @receiver(post_delete, sender="stats.GoogleAnalyticsMetrics")
# def invalidate_stats_cache(sender, instance, **kwargs):
#     """
#     Invalidate stats-related cache when stats models are modified.
#
#     Args:
#         sender: The model class
#         instance: The instance being saved/deleted
#         **kwargs: Additional keyword arguments
#     """
#     try:
#         cache_invalidation_manager.invalidate_stats_cache()
#         logger.info(f"🔄 Invalidated stats cache for model: {sender.__name__}")
#     except Exception as e:
#         logger.error(f"❌ Failed to invalidate stats cache: {e}")


# Social core app not installed - commenting out social cache signals
# @receiver(post_save, sender="social_core.Post")
# @receiver(post_delete, sender="social_core.Post")
# @receiver(post_save, sender="social_core.Comment")
# @receiver(post_delete, sender="social_core.Comment")
# @receiver(post_save, sender="social_core.Reaction")
# @receiver(post_delete, sender="social_core.Reaction")
# def invalidate_social_cache(sender, instance, **kwargs):
#     """
#     Invalidate social-related cache when social models are modified.
#
#     Args:
#         sender: The model class
#         instance: The instance being saved/deleted
#         **kwargs: Additional keyword arguments
#     """
#     try:
#
#         post_id = getattr(instance, "post_id", None) or getattr(instance, "pk", None)
#         if post_id:
#             cache_invalidation_manager.invalidate_post_cache(post_id)
#             logger.info(f"🔄 Invalidated post cache for post ID: {post_id}")
#
#         user_id = getattr(instance, "user_id", None) or getattr(
#             instance, "author_id", None
#         )
#         if user_id:
#             cache_invalidation_manager.invalidate_user_cache(user_id)
#             logger.info(f"🔄 Invalidated user cache for user ID: {user_id}")
#     except Exception as e:
#         logger.error(f"❌ Failed to invalidate social cache: {e}")


# Feed app not installed - commenting out feed cache signals
# @receiver(post_save, sender="feed.FeedItem")
# @receiver(post_delete, sender="feed.FeedItem")
# def invalidate_feed_cache(sender, instance, **kwargs):
#     """
#     Invalidate feed-related cache when feed models are modified.
#
#     Args:
#         sender: The model class
#         instance: The instance being saved/deleted
#         **kwargs: Additional keyword arguments
#     """
#     try:
#
#         user_id = getattr(instance, "user_id", None)
#         if user_id:
#             cache_invalidation_manager.invalidate_user_cache(user_id)
#             logger.info(f"🔄 Invalidated feed cache for user ID: {user_id}")
#
#         cache_invalidation_manager.invalidate_model_cache("post")
#         logger.info(f"🔄 Invalidated feed cache for model: {sender.__name__}")
#     except Exception as e:
#         logger.error(f"❌ Failed to invalidate feed cache: {e}")


# Payment app not installed - commenting out payment cache signals
# @receiver(post_save, sender="payment.Transaction")
# @receiver(post_delete, sender="payment.Transaction")
# @receiver(post_save, sender="payment.Payment")
# @receiver(post_delete, sender="payment.Payment")
# def invalidate_payment_cache(sender, instance, **kwargs):
#     """
#     Invalidate payment-related cache when payment models are modified.
#
#     Args:
#         sender: The model class
#         instance: The instance being saved/deleted
#         **kwargs: Additional keyword arguments
#     """
#     try:
#
#         user_id = getattr(instance, "user_id", None)
#         if user_id:
#             cache_invalidation_manager.invalidate_user_cache(user_id)
#             logger.info(f"🔄 Invalidated payment cache for user ID: {user_id}")
#
#         cache_invalidation_manager.invalidate_model_cache("payment")
#         logger.info(f"🔄 Invalidated payment cache for model: {sender.__name__}")
#     except Exception as e:
#         logger.error(f"❌ Failed to invalidate payment cache: {e}")


# Cards app not installed - commenting out cards cache signals
# @receiver(post_save, sender="cards.Card")
# @receiver(post_delete, sender="cards.Card")
# @receiver(post_save, sender="cards.Collection")
# @receiver(post_delete, sender="cards.Collection")
# def invalidate_cards_cache(sender, instance, **kwargs):
#     """
#     Invalidate cards-related cache when card models are modified.
#
#     Args:
#         sender: The model class
#         instance: The instance being saved/deleted
#         **kwargs: Additional keyword arguments
#     """
#     try:
#
#         user_id = getattr(instance, "user_id", None) or getattr(
#             instance, "owner_id", None
#         )
#         if user_id:
#             cache_invalidation_manager.invalidate_user_cache(user_id)
#             logger.info(f"🔄 Invalidated cards cache for user ID: {user_id}")
#
#         cache_invalidation_manager.invalidate_model_cache("card")
#         logger.info(f"🔄 Invalidated cards cache for model: {sender.__name__}")
#     except Exception as e:
#         logger.error(f"❌ Failed to invalidate cards cache: {e}")


def invalidate_dashboard_cache_for_user(user_id):
    """
    Invalidate dashboard cache for a specific user.

    Args:
        user_id: The user ID to invalidate cache for
    """
    try:
        cache_invalidation_manager.invalidate_dashboard_cache(user_id)
        logger.info(f"🔄 Invalidated dashboard cache for user ID: {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to invalidate dashboard cache: {e}")


@receiver(post_save, sender="notifications.Notification")
@receiver(post_delete, sender="notifications.Notification")
def invalidate_notification_cache(sender, instance, **kwargs):
    """
    Invalidate notification-related cache when notification models are modified.

    Args:
        sender: The model class
        instance: The instance being saved/deleted
        **kwargs: Additional keyword arguments
    """
    try:

        user_id = getattr(instance, "user_id", None) or getattr(
            instance, "recipient_id", None
        )
        if user_id:
            cache_invalidation_manager.invalidate_user_cache(user_id)
            logger.info(f"🔄 Invalidated notification cache for user ID: {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to invalidate notification cache: {e}")
