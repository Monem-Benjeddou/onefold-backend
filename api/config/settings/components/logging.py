"""
Comprehensive logging configuration for the Kolct API project.
Saves ALL log levels (DEBUG through CRITICAL) to separate files.
"""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


if os.path.exists("/logs"):

    LOGS_DIR = Path("/logs")
else:

    LOGS_DIR = BASE_DIR / "logs"
    LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] [{levelname}] [{name}:{lineno}] {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
        "detailed": {
            "format": "[{asctime}] [{levelname}] [{name}:{lineno}] [{funcName}] {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "INFO",
        },
        "debug_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "debug.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "level": "DEBUG",
            "encoding": "utf-8",
        },
        "info_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "info.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "level": "INFO",
            "encoding": "utf-8",
        },
        "warning_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "warning.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "level": "WARNING",
            "encoding": "utf-8",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "error.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "level": "ERROR",
            "encoding": "utf-8",
        },
        "critical_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "critical.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "verbose",
            "level": "CRITICAL",
            "encoding": "utf-8",
        },
        "django_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "django.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "level": "DEBUG",
            "encoding": "utf-8",
        },
        "apps_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "apps.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "level": "DEBUG",
            "encoding": "utf-8",
        },
        "security_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "security.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "verbose",
            "level": "WARNING",
            "encoding": "utf-8",
        },
        "performance_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "performance.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "level": "DEBUG",
            "encoding": "utf-8",
        },
        "celery_beat_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "celery_beat.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "detailed",
            "level": "DEBUG",
            "encoding": "utf-8",
        },
        "celery_tasks_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "celery_tasks.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "detailed",
            "level": "DEBUG",
            "encoding": "utf-8",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "formatter": "verbose",
        },
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "debug_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django": {
            "handlers": [
                "console",
                "django_file",
                "info_file",
                "warning_file",
                "error_file",
            ],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["error_file", "critical_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["security_file", "error_file", "critical_file", "mail_admins"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["performance_file", "warning_file"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": [
                "apps_file",
                "debug_file",
                "info_file",
                "warning_file",
                "error_file",
                "critical_file",
            ],
            "level": "DEBUG",
            "propagate": False,
        },
        "apps.cards.services.vault": {
            "handlers": ["security_file", "apps_file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "vault_service": {
            "handlers": ["security_file", "apps_file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "core": {
            "handlers": [
                "apps_file",
                "debug_file",
                "info_file",
                "warning_file",
                "error_file",
            ],
            "level": "DEBUG",
            "propagate": False,
        },
        "celery": {
            "handlers": [
                "apps_file",
                "debug_file",
                "info_file",
                "warning_file",
                "error_file",
            ],
            "level": "DEBUG",
            "propagate": False,
        },
        "celery.worker": {
            "handlers": [
                "apps_file",
                "debug_file",
                "info_file",
                "warning_file",
                "error_file",
            ],
            "level": "DEBUG",
            "propagate": False,
        },
        "celery.task": {
            "handlers": [
                "celery_tasks_file",
                "apps_file",
                "debug_file",
                "info_file",
                "warning_file",
                "error_file",
            ],
            "level": "DEBUG",
            "propagate": False,
        },
        "celery.beat": {
            "handlers": [
                "celery_beat_file",
                "apps_file",
                "debug_file",
                "info_file",
                "warning_file",
                "error_file",
            ],
            "level": "DEBUG",
            "propagate": False,
        },
        "apps.payment.tasks.bnpl_polling": {
            "handlers": [
                "celery_tasks_file",
                "apps_file",
                "debug_file",
                "info_file",
                "warning_file",
                "error_file",
            ],
            "level": "DEBUG",
            "propagate": False,
        },
        "apps.payment.tasks": {
            "handlers": [
                "celery_tasks_file",
                "apps_file",
                "debug_file",
                "info_file",
                "warning_file",
                "error_file",
            ],
            "level": "DEBUG",
            "propagate": False,
        },
        "performance": {
            "handlers": ["performance_file", "warning_file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}


os.makedirs(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "logs",
    ),
    exist_ok=True,
)


LOGGING_DEV = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": os.environ.get("LOG_LEVEL", "ERROR"),
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": os.environ.get("LOG_LEVEL", "ERROR"),
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                ),
                "logs/django_dev.log",
            ),
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "card_creation": {
            "level": os.environ.get("LOG_LEVEL", "ERROR"),
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                ),
                "logs/card_creation.log",
            ),
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.environ.get("LOG_LEVEL", "ERROR"),
            "propagate": True,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": (
                "DEBUG"
                if os.environ.get("SQL_DEBUG", "False") == "True"
                else os.environ.get("LOG_LEVEL", "ERROR")
            ),
            "propagate": False,
        },
        "api": {
            "handlers": ["console", "file"],
            "level": os.environ.get("LOG_LEVEL", "ERROR"),
            "propagate": False,
        },
        "apps.cards.services.vault": {
            "handlers": ["console", "file"],
            "level": os.environ.get("LOG_LEVEL", "ERROR"),
            "propagate": False,
        },
        "vault_service": {
            "handlers": ["console"],
            "level": os.environ.get("LOG_LEVEL", "ERROR"),
            "propagate": False,
        },
        "apps.cards.celery_tasks": {
            "handlers": ["console", "file", "card_creation"],
            "level": os.environ.get("LOG_LEVEL", "ERROR"),
            "propagate": False,
        },
        "apps.cards.services.bulk_create_service": {
            "handlers": ["console", "file", "card_creation"],
            "level": os.environ.get("LOG_LEVEL", "ERROR"),
            "propagate": False,
        },
        "apps.cards.services.single_create_service": {
            "handlers": ["console", "file", "card_creation"],
            "level": os.environ.get("LOG_LEVEL", "ERROR"),
            "propagate": False,
        },
        "apps.cards.services.card_creation_service": {
            "handlers": ["console", "file", "card_creation"],
            "level": os.environ.get("LOG_LEVEL", "ERROR"),
            "propagate": False,
        },
    },
}


LOGGING_TEST = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
        },
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "api": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps.cards.services.vault": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}


LOGGING_PROD = LOGGING
