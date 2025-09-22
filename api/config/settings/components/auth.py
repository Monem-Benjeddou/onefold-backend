"""
Authentication settings for the Django project.
"""

from decouple import config

AUTH_USER_MODEL = "user.User"

AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "drf_social_oauth2.backends.DjangoOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)


OTP_DELIVERY_METHOD = config("OTP_DELIVERY_METHOD", default="email")


SMS_FALLBACK_TO_EMAIL = config("SMS_FALLBACK_TO_EMAIL", default=True, cast=bool)

OTP_EXPIRATION_MINS = config("OTP_EXPIRATION_MINS", default=10, cast=int)
