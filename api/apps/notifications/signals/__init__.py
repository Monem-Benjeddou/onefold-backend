"""
Notification Signals Package

Organized signal handlers following Django best practices.
Each signal handler is in its own file for better maintainability and readability.
"""

from .notification_signals import *

__all__ = [
    "send_notification",
]
