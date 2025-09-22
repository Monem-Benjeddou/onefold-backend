"""
Enhanced testing settings for Django project with comprehensive isolation.

This configuration focuses on:
1. Complete test isolation (database, cache, filesystem)
2. Automatic resource cleanup and tracking
3. Parallel execution safety
4. Memory optimization for large test suites
5. Factory integration with cleanup
6. Performance monitoring and debugging tools
"""

import os
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent.parent


os.environ["ENV"] = "test"
os.environ["TESTING"] = "true"
os.environ["DEBUG"] = "0"
os.environ["CACHALOT_ENABLED"] = "False"

from .components.paths import GEOIP_PATH
from .components.apps import *
from .components.auth import *
from .components.cache import ENABLE_CACHE
from .components.celery import *
from .components.database import DEFAULT_AUTO_FIELD
from .components.i18n import *


DEBUG = False
TESTING = True
SECRET_KEY = "optimized-test-secret-key-not-for-production"


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

from .components.rest_framework import *
from .components.security import *
from .components.static import *
from .components.templates import *
from .components.urls import *
from .components.app_specific import *
from .components.services import *
from .components.ckeditor import *
from .components.third_party import *
from .components.twilio import *


TESTING = True


SIMPLE_JWT["SIGNING_KEY"] = SECRET_KEY


ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = ["http://testserver"]
SITE_ID = 1


INSTALLED_APPS = [
    app
    for app in INSTALLED_APPS
    if app
    not in [
        "debug_toolbar",
        "silk",
        "django_extensions",
        "cachalot",
    ]
]


for module in [
    "apps.events",
    "apps.events.models",
    "moviepy.editor",
    "moviepy.video.io.VideoFileClip",
    "moviepy.audio.io.AudioFileClip",
    "moviepy.audio.AudioClip",
    "moviepy.audio.io.ffmpeg_audiowriter",
    "moviepy.config",
    "imageio.plugins.ffmpeg",
    "imageio_ffmpeg",
]:
    sys.modules[module] = MagicMock()

os.environ["IMAGEIO_FFMPEG_EXE"] = "ffmpeg"


external_db_vars = ["NEON_DATABASE_URL", "DATABASE_URL", "POSTGRES_URL", "MYSQL_URL"]
for var in external_db_vars:
    if var in os.environ:
        del os.environ[var]


worker_id = os.environ.get("PYTEST_XDIST_WORKER", f"main_{uuid.uuid4().hex[:8]}")


use_concurrent_db = os.environ.get("DJANGO_TEST_CONCURRENT", "false").lower() == "true"

if use_concurrent_db:

    test_db_name = f"/tmp/test_kolct_{worker_id}_{uuid.uuid4().hex[:8]}.sqlite3"
    db_config = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": test_db_name,
        "ATOMIC_REQUESTS": True,
        "OPTIONS": {
            "timeout": 30,
            "check_same_thread": False,
            "isolation_level": "DEFERRED",
        },
        "TEST": {
            "NAME": test_db_name,
            "SERIALIZE": False,
        },
    }
else:

    db_config = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": False,
        "OPTIONS": {
            "timeout": 30,
            "check_same_thread": False,
        },
        "TEST": {
            "NAME": ":memory:",
        },
    }

DATABASES = {"default": db_config}


PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


def get_test_cache_config():
    """Get cache configuration for testing with Redis fallback."""
    try:
        import redis

        redis_host = os.environ.get("REDIS_HOST", "kolct_redis_dev")
        redis_port = os.environ.get("REDIS_PORT", "6379")
        redis_password = os.environ.get("REDIS_PASSWORD")
        redis_db = "1"

        if redis_password:
            redis_url = (
                f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
            )
        else:
            redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

        redis_client = redis.from_url(redis_url)
        redis_client.ping()

        return {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": redis_url,
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                    "CONNECTION_POOL_KWARGS": {
                        "max_connections": 10,
                        "retry_on_timeout": True,
                        "socket_connect_timeout": 3,
                        "socket_timeout": 5,
                    },
                    "IGNORE_EXCEPTIONS": True,
                    "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
                },
                "KEY_PREFIX": f"test_{worker_id}_",
                "VERSION": 1,
                "TIMEOUT": 300,
            }
        }
    except Exception:

        return {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": f"test-cache-{worker_id}",
                "OPTIONS": {
                    "MAX_ENTRIES": 1000,
                    "CULL_FREQUENCY": 2,
                },
            }
        }


CACHES = get_test_cache_config()


SESSION_ENGINE = "django.contrib.sessions.backends.cache"


REST_FRAMEWORK["TEST_REQUEST_DEFAULT_FORMAT"] = "json"
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "nfc_public_key": "10000/min",
    "anon": "10000/hour",
    "user": "10000/hour",
}


MIGRATION_MODULES = {
    "taggit": None,
    "corsheaders": None,
    "rest_framework": None,
    "rest_framework_simplejwt": None,
    "oauth2_provider": None,
    "django_celery_results": None,
    "social_django": None,
    "silk": None,
}


CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"
CELERY_BROKER_CONNECTION_RETRY = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = False
CELERY_BROKER_CONNECTION_TIMEOUT = 1.0
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"


RATE_LIMITER_ENABLED = False
RATE_LIMITER_DEFAULT_RATE = 10000
RATE_LIMITER_DEFAULT_PERIOD = 60


LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "simple",
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
        "root": {
            "handlers": ["null"],
            "level": "CRITICAL",
        },
    },
}


MEDIA_ROOT = tempfile.mkdtemp(prefix="kolct_test_media_")

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": MEDIA_ROOT,
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


OPENAI_API_KEY = "test-openai-key"
SENDGRID_API_KEY = "test-sendgrid-key"
TWILIO_AUTH_TOKEN = "test-twilio-token"
HEYGEN_API_KEY = "test-heygen-api-key"
LMNT_API_KEY = "test-lmnt-api-key"


BLOCKCHAIN_TESTING_ENABLED = True
BLOCKCHAIN_NETWORK = "test"
BLOCKCHAIN_USE_MOCK = True
BLOCKCHAIN_PRIVATE_KEY = "0x" + "0" * 64
CONTRACT_ADDRESS = "0x" + "1" * 40


TEST_ADMIN_EMAIL = "admin@test.com"
TEST_ADMIN_PASSWORD = "testpass123"
TEST_USER_EMAIL = "user@test.com"
TEST_USER_PASSWORD = "testpass123"
TEST_MANUFACTURER_EMAIL = "manufacturer@test.com"
TEST_MANUFACTURER_PASSWORD = "testpass123"


FILE_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024
FILE_UPLOAD_TEMP_DIR = tempfile.mkdtemp(prefix="kolct_test_upload_")


TEST_MEMORY_OPTIMIZATION = True
TEST_BATCH_SIZE = 5
TEST_MAX_OBJECTS = 25


TEST_RUNNER = "core.tests.runners.IsolatedTestRunner"


TEST_ISOLATION_ENABLED = True
TEST_CACHE_ISOLATION = True
TEST_DATABASE_ISOLATION = True
TEST_PARALLEL_SAFETY = True
TEST_MEMORY_OPTIMIZATION_ENABLED = True
TEST_CLEANUP_BETWEEN_TESTS = True


TEST_PARALLEL_WORKERS = int(os.environ.get("DJANGO_TEST_PARALLEL_WORKERS", "2"))
TEST_WORKER_ID = os.environ.get("PYTEST_XDIST_WORKER", f"worker_{os.getpid()}")


TEST_USER_PREFIX = f"test_{uuid.uuid4().hex[:8]}_"
TEST_UNIQUE_SUFFIX = uuid.uuid4().hex[:8]


TEST_PERFORMANCE_MAX_QUERIES = int(os.environ.get("TEST_MAX_QUERIES", "50"))
TEST_PERFORMANCE_MAX_TIME = float(os.environ.get("TEST_MAX_TIME", "5.0"))
TEST_PERFORMANCE_MAX_MEMORY_MB = int(os.environ.get("TEST_MAX_MEMORY_MB", "512"))


CACHES["default"]["OPTIONS"]["KEY_PREFIX"] = f"test_{TEST_WORKER_ID}_"
CACHES["default"]["OPTIONS"]["MAX_ENTRIES"] = 500

import gc

gc.set_threshold(100, 5, 5)


if os.environ.get("CI") or os.environ.get("PYTEST_CURRENT_TEST"):

    gc.set_threshold(50, 3, 3)
    CACHES["default"]["OPTIONS"]["MAX_ENTRIES"] = 200
    TEST_BATCH_SIZE = 3
    TEST_MAX_OBJECTS = 10


STATIC_URL = "/static/"
MEDIA_URL = "/media/"


USE_TZ = True
USE_I18N = False
USE_L10N = False


TEMPLATES[0]["OPTIONS"]["debug"] = False
TEMPLATES[0]["OPTIONS"]["context_processors"] = [
    "django.template.context_processors.debug",
    "django.template.context_processors.request",
    "django.contrib.auth.context_processors.auth",
]


MIDDLEWARE = [
    item
    for item in MIDDLEWARE
    if "SecurityMiddleware" not in item
    and "CsrfViewMiddleware" not in item
    and "ClickjackingMiddleware" not in item
]


DATABASE_CONNECTION_POOLING = {
    "POOL_SIZE": 1,
    "MAX_OVERFLOW": 0,
    "POOL_TIMEOUT": 5,
    "POOL_RECYCLE": 300,
    "POOL_PRE_PING": False,
}


CONN_MAX_AGE = 0
DB_CONN_HEALTH_CHECKS = False


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
USE_I18N = True
USE_L10N = True


TEST_ISOLATION_LEVEL = "read_uncommitted"
TEST_OPTIMIZE_MEMORY = True


OAUTH2_PROVIDER = {
    "ACCESS_TOKEN_MODEL": "oauth2_provider.AccessToken",
    "APPLICATION_MODEL": "oauth2_provider.Application",
    "REFRESH_TOKEN_MODEL": "oauth2_provider.RefreshToken",
}


SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_REFERRER_POLICY = None


ENABLE_CACHE = True
