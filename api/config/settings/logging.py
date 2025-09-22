import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = os.path.join(BASE_DIR, "logs")


LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG").upper()

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(levelname)s:%(name)s:%(message)s",
            "log_colors": {
                "DEBUG": "bold_blue",
                "INFO": "bold_green",
                "WARNING": "bold_yellow",
                "ERROR": "bold_red",
                "CRITICAL": "bold_red,bg_white",
            },
        },
        "simple": {"format": "%(levelname)s %(message)s"},
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "celery": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "colored",
        },
        "django_file": {
            "level": LOG_LEVEL,
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "django.log"),
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "error.log"),
            "formatter": "verbose",
        },
        "celery_file": {
            "level": LOG_LEVEL,
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "celery.log"),
            "formatter": "celery",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "django_file"],
            "level": LOG_LEVEL,
            "propagate": True,
        },
        "celery": {
            "handlers": ["console", "django_file", "celery_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "celery.task": {
            "handlers": ["console", "django_file", "celery_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "celery.worker": {
            "handlers": ["console", "django_file", "celery_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "celery.beat": {
            "handlers": ["console", "django_file", "celery_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "": {
            "handlers": [
                "console",
                "django_file",
                "error_file",
            ],
            "level": LOG_LEVEL,
            "propagate": True,
        },
    },
}
