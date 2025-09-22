"""
Static and media files settings for the project.
"""

import os
from pathlib import Path
from ..config_loader import (
    get_config_value,
    get_env_bool,
    get_environment,
    get_secure_value,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


STATIC_URL = "/static/"
MEDIA_URL = "/media/"

environment = get_environment()


if environment == "testing":
    STATIC_ROOT = os.environ.get("STATIC_ROOT", str(BASE_DIR / "staticfiles"))
    MEDIA_ROOT = os.environ.get("MEDIA_ROOT", str(BASE_DIR / "media"))
elif environment == "production":
    STATIC_ROOT = os.environ.get("STATIC_ROOT", "/var/www/static")
    MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/var/www/media")
else:
    STATIC_ROOT = os.environ.get("STATIC_ROOT", str(BASE_DIR / "staticfiles"))
    MEDIA_ROOT = os.environ.get("MEDIA_ROOT", str(BASE_DIR / "media"))


static_dir = os.path.join(BASE_DIR, "static")
if not get_env_bool("USE_S3", False):
    STATICFILES_DIRS = (
        [static_dir] if os.path.exists(static_dir) and os.listdir(static_dir) else []
    )
else:

    STATICFILES_DIRS = []

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]


USE_S3 = get_env_bool("USE_S3", False)

if USE_S3:

    DO_SPACES_ACCESS_KEY_ID = get_secure_value("DO_SPACES_ACCESS_KEY_ID", "")
    DO_SPACES_SECRET_ACCESS_KEY = get_secure_value("DO_SPACES_SECRET_ACCESS_KEY", "")
    DO_SPACES_BUCKET_NAME = get_secure_value("DO_SPACES_BUCKET_NAME", "")
    DO_SPACES_ENDPOINT_URL = get_secure_value("DO_SPACES_ENDPOINT_URL", "")
    DO_SPACES_REGION_NAME = get_secure_value("DO_SPACES_REGION_NAME", "fra1")
    DO_SPACES_CUSTOM_DOMAIN = get_secure_value("DO_SPACES_CUSTOM_DOMAIN", "")

    AWS_ACCESS_KEY_ID = DO_SPACES_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = DO_SPACES_SECRET_ACCESS_KEY
    AWS_STORAGE_BUCKET_NAME = DO_SPACES_BUCKET_NAME
    AWS_S3_ENDPOINT_URL = DO_SPACES_ENDPOINT_URL
    AWS_S3_REGION_NAME = DO_SPACES_REGION_NAME
    AWS_S3_CUSTOM_DOMAIN = DO_SPACES_CUSTOM_DOMAIN

    AWS_DEFAULT_ACL = "public-read"
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False

    AWS_S3_MAX_POOL_CONNECTIONS = 50
    AWS_S3_CONNECT_TIMEOUT = 5
    AWS_S3_READ_TIMEOUT = 10
    AWS_S3_RETRY_TOTAL_ATTEMPTS = 3
    AWS_S3_RETRY_MODE = "adaptive"

    STATIC_LOCATION = "static"
    STATIC_URL = f"https://{DO_SPACES_CUSTOM_DOMAIN}/{STATIC_LOCATION}/"

    STORAGES = {
        "default": {
            "BACKEND": "config.storage_backends.MediaStorage",
        },
        "staticfiles": {
            "BACKEND": "config.storage_backends.StaticStorage",
        },
    }

    MEDIA_LOCATION = "media"
    MEDIA_URL = f"https://{DO_SPACES_CUSTOM_DOMAIN}/{MEDIA_LOCATION}/"

    print(f"✅ DigitalOcean Spaces storage configured")
    print(f"   Bucket: {DO_SPACES_BUCKET_NAME}")
    print(f"   Region: {DO_SPACES_REGION_NAME}")
    print(f"   Static URL: {STATIC_URL}")
    print(f"   Media URL: {MEDIA_URL}")
else:

    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    print("📁 Using local file storage for static and media files")
