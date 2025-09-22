"""
Configuration for third-party services like Twilio, Vonage, Google Analytics.
"""

import os
from decouple import config
from config.settings.components.paths import BASE_DIR
from ..config_loader import get_redis_config, get_celery_config


TWILIO_ACCOUNT_SID = config("TWILIO_SID", default="AC1234567890")
TWILIO_MESSAGING_SID = config("TWILIO_MESSAGING_SID", default="MG1234567890")
TWILIO_AUTH_TOKEN = config("TWILIO_AUTH_TOKEN", default="1234567890")
TWILIO_NUMBER = config("TWILIO_NUMBER", default="+1234567890")
TWILIO_TEST_AUTH_TOKEN = config("TWILIO_TEST_AUTH_TOKEN", default="1234567890")
TWILIO_TEST_SID = config("TWILIO_TEST_SID", default="AC1234567890")
TWILIO_VERIFY_SERVICE_SID = config("TWILIO_VERIFY_SERVICE_SID", default="VA1234567890")


VONAGE_API_KEY = config("VONAGE_API_KEY", default="1234567890")
VONAGE_API_SECRET = config("VONAGE_API_SECRET", default="1234567890")
VONAGE_FROM = config("VONAGE_FROM", default="1234567890")


NEONS_SMS_BASE_URL = config(
    "NEONS_SMS_BASE_URL", default="https://neons-stg-integrationgateway.neons.sa"
)
NEONS_SMS_AUTH_URL = config("NEONS_SMS_AUTH_URL", default="")
NEONS_SMS_CLIENT_ID = config("NEONS_SMS_CLIENT_ID", default="")
NEONS_SMS_CLIENT_SECRET = config("NEONS_SMS_CLIENT_SECRET", default="")
NEONS_SMS_TOKEN_CACHE_TTL = config("NEONS_SMS_TOKEN_CACHE_TTL", default=3600, cast=int)


GOOGLE_ANALYTICS_PROPERTY_ID = config("PROPRTY_ID", default=None)
GOOGLE_SERVICE_ACCOUNT_EMAIL_ADDRESS = config(
    "GOOGLE_SERVICE_ACCOUNT_EMAIL_ADDRESS", default=None
)
GOOGLE_SERVICE_JSON_FILE_PATH = config("GOOGLE_SERVICE_JSON_FILE_PATH", default=None)


GOOGLE_ANALYTICS_SERVICE_ACCOUNT_FILE = os.environ.get(
    "GOOGLE_ANALYTICS_SERVICE_ACCOUNT_FILE", "config/awqaf-credentials.json"
)
GOOGLE_ANALYTICS_CREDENTIALS = {
    "token": os.environ.get("GOOGLE_ANALYTICS_TOKEN"),
    "refresh_token": os.environ.get("GOOGLE_ANALYTICS_REFRESH_TOKEN"),
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": os.environ.get("GOOGLE_ANALYTICS_CLIENT_ID"),
    "client_secret": os.environ.get("GOOGLE_ANALYTICS_CLIENT_SECRET"),
    "scopes": ["https://www.googleapis.com/auth/analytics.readonly"],
}


NEO_SNB_BASE_URL = config(
    "NEO_SNB_BASE_URL", default="https://api-bnpl-uat.neo.sa:8885"
)
NEO_SNB_CHECKOUT_URL = config(
    "NEO_SNB_CHECKOUT_URL",
    default="https://checkout-bnpl-uat.neo.sa:8886",
)
NEO_SNB_PUBLIC_KEY = config("NEO_SNB_PUBLIC_KEY", default="test-public-key")
NEO_SNB_PRIVATE_KEY = config("NEO_SNB_PRIVATE_KEY", default="test-private-key")
NEO_SNB_USE_MOCK = config("NEO_SNB_USE_MOCK", default=True, cast=bool)
NEO_SNB_TIMEOUT = config("NEO_SNB_TIMEOUT", default=30, cast=int)


redis_config = get_redis_config()
celery_config = get_celery_config()

REDIS_HOST = redis_config["HOST"]
REDIS_PORT = redis_config["PORT"]
REDIS_DB = redis_config["cache"]["DB"]
REDIS_PASSWORD = redis_config["PASSWORD"]


use_do_redis = os.environ.get("USE_DO_REDIS", "false").lower() == "true"

if use_do_redis:

    if (
        "USERNAME" in redis_config
        and redis_config["USERNAME"]
        and redis_config["PASSWORD"]
    ):
        REDIS_URL = f"rediss://{redis_config['USERNAME']}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    elif REDIS_PASSWORD:
        REDIS_URL = f"rediss://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    else:
        REDIS_URL = f"rediss://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
else:

    if (
        "USERNAME" in redis_config
        and redis_config["USERNAME"]
        and redis_config["PASSWORD"]
    ):
        REDIS_URL = f"redis://{redis_config['USERNAME']}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    elif REDIS_PASSWORD:
        REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    else:
        REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

Q_CLUSTER = {
    "name": "DjangORM",
    "workers": 4,
    "timeout": 90,
    "retry": 120,
    "queue_limit": 50,
    "bulk": 10,
    "orm": "default",
}

import sys

TESTING = "test" in sys.argv or "pytest" in sys.modules

if TESTING:

    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
else:

    if use_do_redis:

        if (
            "USERNAME" in redis_config
            and redis_config["USERNAME"]
            and redis_config["PASSWORD"]
        ):
            redis_hosts = [
                f"rediss://{redis_config['USERNAME']}:{redis_config['PASSWORD']}@{REDIS_HOST}:{REDIS_PORT}/0"
            ]
        elif REDIS_PASSWORD:
            redis_hosts = [f"rediss://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"]
        else:
            redis_hosts = [f"rediss://{REDIS_HOST}:{REDIS_PORT}/0"]
    else:

        if (
            "USERNAME" in redis_config
            and redis_config["USERNAME"]
            and redis_config["PASSWORD"]
        ):
            redis_hosts = [
                f"redis://{redis_config['USERNAME']}:{redis_config['PASSWORD']}@{REDIS_HOST}:{REDIS_PORT}/0"
            ]
        elif REDIS_PASSWORD:
            redis_hosts = [f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"]
        else:
            redis_hosts = [(REDIS_HOST, REDIS_PORT)]

    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": redis_hosts,
                "capacity": 1500,
                "expiry": 10,
                "group_expiry": 86400,
                "symmetric_encryption_keys": [
                    os.environ.get("CHANNELS_SECRET_KEY", "your-secret-key-here")
                ],
            },
        },
    }
