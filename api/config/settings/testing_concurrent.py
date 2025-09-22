"""
Testing settings specifically optimized for concurrent/threading tests.

This configuration provides:
1. File-based SQLite database with WAL mode for better concurrent access
2. Redis cache for true distributed locking
3. Proper transaction isolation settings
4. Thread-safe configurations
"""

import os
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent.parent


from .components.paths import GEOIP_PATH
from .components.apps import *
from .components.auth import *
from .components.cache import ENABLE_CACHE
from .components.celery import *
from .components.database import DEFAULT_AUTO_FIELD
from .components.i18n import *


from .components.debug_config import DEBUG

TESTING = True
SECRET_KEY = "concurrent-test-secret-key-not-for-production"


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
os.environ["ENV"] = "test"
os.environ["TESTING"] = "true"


external_db_vars = ["NEON_DATABASE_URL", "DATABASE_URL", "POSTGRES_URL", "MYSQL_URL"]
for var in external_db_vars:
    if var in os.environ:
        del os.environ[var]


worker_id = os.environ.get("PYTEST_XDIST_WORKER", f"main_{uuid.uuid4().hex[:8]}")


test_db_name = f"/tmp/test_kolct_concurrent_{worker_id}_{uuid.uuid4().hex[:8]}.sqlite3"

DATABASES = {
    "default": {
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
    },
}


def get_concurrent_test_cache_config():
    """Get Redis cache configuration for concurrent testing."""
    try:

        import redis

        redis_url = os.environ.get("REDIS_URL", "redis://kolct_redis_dev:6379/2")
        redis_client = redis.from_url(redis_url)
        redis_client.ping()

        return {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": redis_url,
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                    "CONNECTION_POOL_KWARGS": {
                        "max_connections": 20,
                        "retry_on_timeout": True,
                        "socket_connect_timeout": 5,
                        "socket_timeout": 10,
                    },
                    "IGNORE_EXCEPTIONS": False,
                    "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
                },
                "KEY_PREFIX": f"concurrent_test_{worker_id}_",
                "VERSION": 1,
                "TIMEOUT": 300,
            }
        }
    except Exception as e:
        print(f"Warning: Redis not available for concurrent tests: {e}")
        print("Falling back to locmem cache - distributed locking will be simulated")

        return {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": f"concurrent_test_cache_{worker_id}",
                "OPTIONS": {
                    "MAX_ENTRIES": 5000,
                    "CULL_FREQUENCY": 2,
                },
            }
        }


CACHES = get_concurrent_test_cache_config()


from .components.rest_framework import *
from .components.security import *
from .components.static import *
from .components.templates import *
from .components.urls import *
from .components.app_specific import *
from .components.services import *
from .components.ckeditor import *
from .components.third_party import *


SIMPLE_JWT["SIGNING_KEY"] = SECRET_KEY


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


ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = ["http://testserver"]
SITE_ID = 1


INSTALLED_APPS = [
    app
    for app in INSTALLED_APPS
    if app not in ["debug_toolbar", "silk", "django_extensions"]
]


PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


SESSION_ENGINE = "django.contrib.sessions.backends.cache"


REST_FRAMEWORK["TEST_REQUEST_DEFAULT_FORMAT"] = "json"
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "nfc_public_key": "10000/min",
    "anon": "10000/hour",
    "user": "10000/hour",
}


MIGRATION_MODULES = {
    "cards": None,
    "auth": None,
    "contenttypes": None,
    "sessions": None,
    "admin": None,
    "messages": None,
    "taggit": None,
    "corsheaders": None,
    "rest_framework": None,
    "rest_framework_simplejwt": None,
    "oauth2_provider": None,
    "payment": None,
    "feed": None,
    "social_core": None,
    "relationships": None,
    "core": None,
    "notifications": None,
    "files": None,
    "video_ai": None,
    "privacy": None,
    "manifacturer": None,
    "wallet": None,
    "stats": None,
    "salesman": None,
    "waitlist": None,
    "social_analytics": None,
    "search": None,
    "internationalization": None,
}


CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"


RATE_LIMITER_ENABLED = False
RATE_LIMITER_DEFAULT_RATE = 10000
RATE_LIMITER_DEFAULT_PERIOD = 60


LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
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
        "apps.payment.services.ownership_transfer": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "root": {
            "handlers": ["null"],
            "level": "CRITICAL",
        },
    },
}


MEDIA_ROOT = tempfile.mkdtemp(prefix="kolct_concurrent_test_media_")
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
FILE_UPLOAD_TEMP_DIR = tempfile.mkdtemp(prefix="kolct_concurrent_test_upload_")


TEST_RUNNER = "core.tests.runners.IsolatedTestRunner"


TEST_CONCURRENT_ENABLED = True
TEST_ISOLATION_ENABLED = True
TEST_CACHE_ISOLATION = True
TEST_DATABASE_ISOLATION = True
TEST_PARALLEL_SAFETY = True
TEST_MEMORY_OPTIMIZATION_ENABLED = False
TEST_CLEANUP_BETWEEN_TESTS = True


CONN_MAX_AGE = 0
DB_CONN_HEALTH_CHECKS = False


TEST_PERFORMANCE_MAX_QUERIES = 200
TEST_PERFORMANCE_MAX_TIME = 30.0
TEST_PERFORMANCE_MAX_MEMORY_MB = 1024


STATIC_URL = "/static/"
MEDIA_URL = "/media/"


USE_TZ = True
USE_I18N = True
USE_L10N = True


TEMPLATES[0]["OPTIONS"]["debug"] = False
TEMPLATES[0]["OPTIONS"]["context_processors"] = [
    "django.template.context_processors.debug",
    "django.template.context_processors.request",
    "django.contrib.auth.context_processors.auth",
]


SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_REFERRER_POLICY = None


OAUTH2_PROVIDER = {
    "ACCESS_TOKEN_MODEL": "oauth2_provider.AccessToken",
    "APPLICATION_MODEL": "oauth2_provider.Application",
    "REFRESH_TOKEN_MODEL": "oauth2_provider.RefreshToken",
}


ENABLE_CACHE = True

print(f"🔧 Concurrent test configuration loaded for worker: {worker_id}")
print(f"📦 Database: {test_db_name}")
print(f"🔄 Cache backend: {CACHES['default']['BACKEND']}")
