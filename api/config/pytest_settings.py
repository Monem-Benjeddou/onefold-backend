"""
Pytest-specific settings for Django.
This file is used only for running tests with pytest.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = "django-insecure-test-key-for-pytest"


DEBUG = False


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "rest_framework.authtoken",
    "django_countries",
    "phonenumber_field",
    "oauth2_provider",
    "core",
    "apps.accounts.user",
    "apps.accounts.auth",
    "apps.accounts.founder",
    "apps.company",
    "apps.competitor",
    "apps.countries",
    "apps.files",
    "apps.funding",
    "apps.internationalization",
    "apps.notifications",
    "apps.privacy",
    "apps.revenue",
    "apps.stakeholder",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "api.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "api.config.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {
            "timeout": 30,
            "check_same_thread": False,
        },
        "TEST": {
            "NAME": ":memory:",
            "MIRROR": None,
        },
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATIC_ROOT = "/tmp/static/"
MEDIA_URL = "media/"
MEDIA_ROOT = "/tmp/media/"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


AUTH_USER_MODEL = "user.User"


SITE_ID = 1


EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
DEFAULT_FROM_EMAIL = "test@example.com"
EMAIL_TEST = "test@example.com"


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}


sys.modules["moviepy.editor"] = MagicMock()
sys.modules["moviepy.video.io.VideoFileClip"] = MagicMock()
sys.modules["moviepy.audio.io.AudioFileClip"] = MagicMock()
sys.modules["moviepy.audio.AudioClip"] = MagicMock()
sys.modules["moviepy.audio.io.ffmpeg_audiowriter"] = MagicMock()
sys.modules["moviepy.config"] = MagicMock()
sys.modules["imageio.plugins.ffmpeg"] = MagicMock()
sys.modules["imageio_ffmpeg"] = MagicMock()


os.environ["IMAGEIO_FFMPEG_EXE"] = "ffmpeg"


# Disable problematic migrations for SQLite testing
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()


PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


CELERY_ALWAYS_EAGER = True


ALLOWED_HOSTS = ["*"]

# Additional SQLite-specific settings for testing
USE_TZ = True
TIME_ZONE = "UTC"

# Disable some features that might cause issues with SQLite
DATABASE_ROUTERS = []

# Ensure we're using SQLite for all operations
DATABASE_CONNECTION_POOLING = None
