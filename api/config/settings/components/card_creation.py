"""
Card creation mode configuration settings.

This module handles the toggleable card creation system that allows
switching between single_create and bulk_create modes.
"""

import os
from django.core.exceptions import ImproperlyConfigured


def get_bool_env(var_name, default=False):
    """Convert environment variable to boolean."""
    value = os.getenv(var_name, str(default))
    if value is None:
        return default
    return str(value).lower() in ("true", "1", "yes", "on")


def get_int_env(var_name, default):
    """Convert environment variable to integer."""
    value = os.getenv(var_name, str(default))
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


CARD_CREATION_MODE = os.getenv("CARD_CREATION_MODE", "single_create")


VALID_CARD_CREATION_MODES = ["single_create", "bulk_create"]
if CARD_CREATION_MODE not in VALID_CARD_CREATION_MODES:
    raise ImproperlyConfigured(
        f"CARD_CREATION_MODE must be one of {VALID_CARD_CREATION_MODES}, "
        f"got '{CARD_CREATION_MODE}'"
    )


BULK_CREATE_PARALLEL_WORKERS = get_int_env("BULK_CREATE_PARALLEL_WORKERS", 4)
BULK_CREATE_BATCH_SIZE = get_int_env("BULK_CREATE_BATCH_SIZE", 100)


BULK_CREATE_PROGRESS_UPDATES_ENABLED = get_bool_env(
    "BULK_CREATE_PROGRESS_UPDATES_ENABLED", True
)


SERIAL_NUMBER_USE_UUID_FALLBACK = get_bool_env("SERIAL_NUMBER_USE_UUID_FALLBACK", False)
SERIAL_NUMBER_MAX_RETRIES = get_int_env("SERIAL_NUMBER_MAX_RETRIES", 10)


CARD_CREATION_SINGLE_MODE_ENABLED = CARD_CREATION_MODE == "single_create"
CARD_CREATION_BULK_MODE_ENABLED = CARD_CREATION_MODE == "bulk_create"


if CARD_CREATION_MODE == "bulk_create":

    CARD_CREATION_USE_SIGNALS = False

    CARD_CREATION_PARALLEL_PROCESSING = True
else:

    CARD_CREATION_USE_SIGNALS = True

    CARD_CREATION_PARALLEL_PROCESSING = False


CARD_CREATION_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "card_creation": {
            "format": "[{asctime}] {levelname} [{name}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "card_creation_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "card_creation.log",
            "formatter": "card_creation",
        },
    },
    "loggers": {
        "apps.cards.services.card_creation": {
            "handlers": ["card_creation_file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
