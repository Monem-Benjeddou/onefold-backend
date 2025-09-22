"""
Third-party app settings for the project.
"""

import os
from ..config_loader import get_aws_config, get_config_value


SHELL_PLUS = "ipython"
SHELL_PLUS_PRINT_SQL = True
SHELL_PLUS_IMPORTS = [
    "from django.core.cache import cache",
    "from django.conf import settings",
    "from django.contrib.auth.models import User",
    "from django.db.models import Avg, Case, Count, F, Max, Min, Prefetch, Q, Sum, When",
    "from django.utils import timezone",
]


aws_config = get_aws_config()
AWS_ACCESS_KEY_ID = aws_config["ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = aws_config["SECRET_ACCESS_KEY"]
AWS_STORAGE_BUCKET_NAME = aws_config["STORAGE_BUCKET_NAME"]
AWS_S3_REGION_NAME = aws_config["S3_REGION_NAME"]
AWS_S3_SIGNATURE_VERSION = aws_config["S3_SIGNATURE_VERSION"]
AWS_S3_FILE_OVERWRITE = aws_config["S3_FILE_OVERWRITE"]
AWS_DEFAULT_ACL = aws_config["DEFAULT_ACL"]
AWS_S3_VERIFY = aws_config["S3_VERIFY"]


CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL_ORIGINS", "False") == "True"
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
CORS_ALLOW_CREDENTIALS = True


ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = "/"
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_USERNAME_BLACKLIST = ["admin", "administrator", "root", "superuser"]
ACCOUNT_USERNAME_MIN_LENGTH = 3


oauth_config = get_config_value("oauth", {})
SOCIAL_AUTH_POSTGRES_JSONFIELD = oauth_config.get("postgres_jsonfield", True)
SOCIAL_AUTH_URL_NAMESPACE = oauth_config.get("url_namespace", "social")
SOCIAL_AUTH_LOGIN_REDIRECT_URL = oauth_config.get("login_redirect_url", "/")
SOCIAL_AUTH_LOGIN_ERROR_URL = oauth_config.get("login_error_url", "/login-error/")
SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = oauth_config.get(
    "admin_user_search_fields", ["username", "first_name", "email"]
)
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = oauth_config.get("username_is_full_email", True)


SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get(
    "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", ""
)
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


SOCIAL_AUTH_FACEBOOK_KEY = os.environ.get("SOCIAL_AUTH_FACEBOOK_KEY", "")
SOCIAL_AUTH_FACEBOOK_SECRET = os.environ.get("SOCIAL_AUTH_FACEBOOK_SECRET", "")
SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {"fields": "id, name, email"}


health_config = get_config_value("health_check", {})
HEALTH_CHECK = {
    "DISK_USAGE_MAX": health_config.get("disk_usage_max", 90),
    "MEMORY_MIN": health_config.get("memory_min", 100),
}


axes_config = get_config_value("axes", {})
AXES_FAILURE_LIMIT = int(
    os.environ.get("AXES_FAILURE_LIMIT", axes_config.get("failure_limit", 5))
)
AXES_LOCK_OUT_AT_FAILURE = (
    os.environ.get(
        "AXES_LOCK_OUT_AT_FAILURE", str(axes_config.get("lock_out_at_failure", True))
    ).lower()
    == "true"
)
AXES_COOLOFF_TIME = int(
    os.environ.get("AXES_COOLOFF_TIME", axes_config.get("cooloff_time", 1))
)
AXES_USE_USER_AGENT = (
    os.environ.get(
        "AXES_USE_USER_AGENT", str(axes_config.get("use_user_agent", True))
    ).lower()
    == "true"
)
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = (
    os.environ.get(
        "AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP",
        str(axes_config.get("lock_out_by_combination_user_and_ip", True)),
    ).lower()
    == "true"
)
AXES_RESET_ON_SUCCESS = (
    os.environ.get(
        "AXES_RESET_ON_SUCCESS", str(axes_config.get("reset_on_success", True))
    ).lower()
    == "true"
)
AXES_ONLY_ADMIN_SITE = (
    os.environ.get(
        "AXES_ONLY_ADMIN_SITE", str(axes_config.get("only_admin_site", False))
    ).lower()
    == "true"
)


MOYASAR_SECRET_KEY = os.environ.get("MOYASAR_SECRET_KEY") or os.environ.get(
    "MOYASSAR_SECRET_KEY", ""
)
MOYASAR_PUBLISHABLE_KEY = os.environ.get("MOYASAR_PUBLISHABLE_KEY") or os.environ.get(
    "MOYASSAR_PUBLISHABLE_KEY", ""
)
MOYASSAR_SECRET_TOKEN = os.environ.get("MOYASSAR_SECRET_TOKEN", "")
MOYASAR_API_KEY = os.environ.get("MOYASAR_API_KEY", "")
