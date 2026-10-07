"""Test settings: fast, isolated, no external services."""

import os

os.environ.setdefault("DEBUG", "1")
os.environ.pop("REDIS_URL", None)

from .settings import *  # noqa: E402,F403

if os.environ.get("TEST_USE_SQLITE", "1") == "1":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
FRONTEND_URL = "https://app.onefold.test"
SECRET_KEY = "test-secret-key-that-is-long-enough-for-hs256"
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m]
