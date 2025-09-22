"""
App-specific settings for the project.
"""

import os
from .paths import BASE_DIR
from ..config_loader import get_config_value, get_frontend_config, get_environment


ALLOWED_HEADERS = get_config_value(
    "allowed_headers", os.environ.get("ALLOWED_HEADERS", default="*")
)

DEFAULT_AVATAR_URL = "https://avatars.dicebear.com/api/identicon/.svg"
OVERRIDE_FILE_UPLOAD_NAME = True


frontend_config = get_frontend_config()
environment = get_environment()

FRONTEND_URL = frontend_config["URL"]
JURY_FRONTEND_URL = frontend_config["UI_URLS"]["JURY"] or FRONTEND_URL
CANDIDATE_FRONTEND_URL = frontend_config["UI_URLS"]["CANDIDATE"] or FRONTEND_URL
ADMIN_FRONTEND_URL = frontend_config["UI_URLS"]["ADMIN"] or FRONTEND_URL

CONTENT_TYPES = get_config_value("content_types", {})

STORYBOOK_PORT = get_config_value("storybook.port", 6006)

RATE_LIMITER_ENABLED = get_config_value("rate_limiter.enabled", False)
RATE_LIMIT_DEFAULT = get_config_value("rate_limiter.default_rate", "100/day")
RATE_LIMIT_SENSITIVE = get_config_value("rate_limiter.sensitive_rate", "10/minute")

SITE_NAME = get_config_value("site.name", "Kolct")
SITE_URL = get_config_value(f"site.{environment}.url", f"site.url")

ADMIN_EMAIL = get_config_value("admin.email", "admin@yourdomain.com")


JURY_ASSIGNMENT_LIMIT = int(os.environ.get("JURY_ASSIGNMENT_LIMIT", default=3))
JURY_LIKE_COUNT_LIMIT = int(os.environ.get("JURY_LIKE_COUNT_LIMIT", default=1500))
JURY_SELECT_COUNT_LIMIT = int(os.environ.get("JURY_SELECT_COUNT_LIMIT", default=20))
JURY_FEEDBACK_COUNT_LIMIT = int(
    os.environ.get("JURY_FEEDBACK_COUNT_LIMIT", default=500)
)
JURY_REJECT_COUNT_LIMIT = int(os.environ.get("JURY_REJECT_COUNT_LIMIT", default=1500))
WINNERS_COUNT_LIMIT = int(os.environ.get("WINNERS_COUNT_LIMIT", default=20))
TOP_WINNER_COUNT = int(os.environ.get("TOP_WINNER_COUNT", 5))


CARDS_ADMIN_VERIFY_TOKEN = os.environ.get("CARDS_ADMIN_VERIFY_TOKEN", "")


VISITOR_TRACKING = {
    "TRACK_API_REQUESTS": True,
    "TRACK_ADMIN_REQUESTS": False,
    "TRACK_STATIC_REQUESTS": False,
    "TRACK_MEDIA_REQUESTS": False,
}


ASYNC_REQUEST_TIMEOUT = int(os.environ.get("ASYNC_REQUEST_TIMEOUT", default=60))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", default=60))
CHANNEL_EXPIRY_SECONDS = int(os.environ.get("CHANNEL_EXPIRY_SECONDS", default=60))


RATE_LIMITER_DEFAULT_RATE = int(os.environ.get("RATE_LIMITER_DEFAULT_RATE", default=5))
RATE_LIMITER_DEFAULT_PERIOD = int(
    os.environ.get("RATE_LIMITER_DEFAULT_PERIOD", default=1)
)


CARDS_ADMIN_VERIFY_TOKEN = os.environ.get("CARDS_ADMIN_VERIFY_TOKEN", "")


NFC_DERIVE_BASE_URL = os.environ.get(
    "NFC_DERIVE_BASE_URL",
    "https://kolct-derive-311840642308.europe-west1.run.app/",
)

NEO_DG_USERNAME = os.environ.get("NEO_DG_USERNAME", "dgneo")
