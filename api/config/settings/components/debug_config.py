"""
DEBUG configuration - Single source of truth.

This module ensures DEBUG mode is controlled exclusively by the DEBUG environment variable
across all environments (development, staging, production, testing).
"""

import os
import logging
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def get_debug_mode() -> bool:
    """
    Get DEBUG mode exclusively from environment variable.

    Returns:
        bool: DEBUG mode based on environment variable only

    Raises:
        ImproperlyConfigured: If DEBUG environment variable is not set

    Security Note:
        - No fallback defaults to prevent accidental DEBUG=True in production
        - Explicit configuration required for all environments
        - Environment variable must be explicitly set
    """
    debug_value = os.environ.get("DEBUG")
    env_name = os.environ.get("ENV", "unknown")

    if env_name == "test" or os.environ.get("TESTING", "").lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        logger.info("Testing environment detected - forcing DEBUG=False")
        os.environ["DEBUG"] = "0"
        return False

    if debug_value is None:
        environment = os.environ.get("ENV", "unknown")
        raise ImproperlyConfigured(
            f"DEBUG environment variable is not set for environment '{environment}'. "
            f"Please set DEBUG=1 (True) or DEBUG=0 (False) in your environment file.\n"
            f"Examples:\n"
            f"  Development: DEBUG=1\n"
            f"  Production: DEBUG=0\n"
            f"  Testing: DEBUG=0"
        )

    debug_bool = debug_value.lower() in ("1", "true", "yes", "on")

    logger.info(
        f"DEBUG mode set to {debug_bool} for environment '{env_name}' (DEBUG={debug_value})"
    )

    return debug_bool


DEBUG = get_debug_mode()


__all__ = ["DEBUG", "get_debug_mode"]
