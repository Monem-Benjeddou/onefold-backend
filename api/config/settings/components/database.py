"""
Database settings for the project.
"""

import os
from pathlib import Path
from ..config_loader import get_environment, get_database_config

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

ENVIRONMENT = get_environment()


if ENVIRONMENT == "testing":

    import tempfile
    import uuid
    import os

    worker_id = os.environ.get("PYTEST_XDIST_WORKER", f"main_{uuid.uuid4().hex[:8]}")
    temp_dir = tempfile.gettempdir()
    db_file = f"{temp_dir}/test_db_{worker_id}.sqlite3"

    db_config = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": db_file,
        "CONN_MAX_AGE": 0,
        "ATOMIC_REQUESTS": False,
        "OPTIONS": {
            "timeout": 30,
            "check_same_thread": False,
            "isolation_level": None,
        },
        "TEST": {
            "NAME": db_file,
            "OPTIONS": {
                "timeout": 30,
                "check_same_thread": False,
                "isolation_level": None,
            },
            "MIRROR": None,
        },
    }
else:
    db_config = get_database_config()


if db_config.get("ENGINE") == "django.db.backends.sqlite3":

    DATABASES = {"default": db_config}
else:

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_config.get("NAME", "postgres"),
            "USER": db_config.get("USER", "postgres"),
            "PASSWORD": db_config.get("PASSWORD", "postgres"),
            "HOST": db_config.get("HOST", "localhost"),
            "PORT": db_config.get("PORT", 5432),
            "CONN_MAX_AGE": 600,
            "ATOMIC_REQUESTS": False,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
                "isolation_level": 2,
                "server_side_binding": True,
            },
            "TEST": {
                "MIRROR": None,
            },
        },
    }


DATABASE_CONNECTION_POOLING = {
    "POOL_SIZE": 20,
    "MAX_OVERFLOW": 10,
    "POOL_TIMEOUT": 30,
    "POOL_RECYCLE": 3600,
    "POOL_PRE_PING": True,
}


if ENVIRONMENT != "testing" and "TEST" in db_config and db_config["TEST"]:
    test_config = (
        db_config["TEST"].copy() if isinstance(db_config["TEST"], dict) else {}
    )

    if "MIRROR" not in test_config:
        test_config["MIRROR"] = None

    if test_config:
        DATABASES["default"]["TEST"].update(test_config)

DATABASES_TEST = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "TEST": {
            "MIRROR": None,
        },
    }
}

DATABASES_DEV = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "TEST": {
            "MIRROR": None,
        },
    }
}

DATABASES_PROD = {
    "default": {
        "ENGINE": db_config.get("ENGINE", "django.db.backends.postgresql"),
        "NAME": db_config.get("NAME", "postgres"),
        "USER": db_config.get("USER", "postgres"),
        "PASSWORD": db_config.get("PASSWORD", "postgres"),
        "HOST": db_config.get("HOST", "localhost"),
        "PORT": db_config.get("PORT", 5432),
        "CONN_MAX_AGE": db_config.get("CONN_MAX_AGE", 600),
        "ATOMIC_REQUESTS": db_config.get("ATOMIC_REQUESTS", False),
        "OPTIONS": db_config.get(
            "OPTIONS",
            {
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            },
        ),
        "TEST": {
            "MIRROR": None,
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
