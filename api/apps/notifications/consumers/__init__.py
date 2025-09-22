"""
Notification Consumers Package

Organized WebSocket consumers following Django Channels best practices.
Each consumer is in its own file for better maintainability and readability.
"""

import logging
from django.core.cache import cache

from .notification_consumer import NotificationConsumer


logger = logging.getLogger(__name__)

__all__ = [
    "NotificationConsumer",
    "cache",
    "logger",
]
