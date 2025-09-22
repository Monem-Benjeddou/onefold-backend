"""
Email backend configurations for different environments.
"""

import os
from django.core.mail.backends.smtp import EmailBackend


EMAIL_HOST = os.environ.get("EMAIL_HOST", "mail.neoevents.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "no-reply@neoevents.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")


EMAIL_ACTIVATION_HOST = os.environ.get(
    "EMAIL_ACTIVATION_HOST", "your_account_activation@neoevents.com"
)
EMAIL_ACTIVATION_PASSWORD = os.environ.get("EMAIL_ACTIVATION_PASSWORD", "")


def get_activation_backend():
    """Get the email backend for activation emails."""
    return EmailBackend(
        host=EMAIL_HOST,
        port=int(os.environ.get("EMAIL_ACTIVATION_PORT", 465)),
        username=EMAIL_ACTIVATION_HOST,
        password=EMAIL_ACTIVATION_PASSWORD,
        use_tls=os.environ.get("EMAIL_ACTIVATION_USE_TLS", "False") == "True",
        use_ssl=os.environ.get("EMAIL_ACTIVATION_USE_SSL", "True") == "True",
    )


def get_no_reply_backend():
    """Get the email backend for no-reply emails."""
    return EmailBackend(
        host=EMAIL_HOST,
        port=int(os.environ.get("EMAIL_NO_REPLY_PORT", 465)),
        username=EMAIL_HOST_USER,
        password=EMAIL_HOST_PASSWORD,
        use_tls=os.environ.get("EMAIL_NO_REPLY_USE_TLS", "False") == "True",
        use_ssl=os.environ.get("EMAIL_NO_REPLY_USE_SSL", "True") == "True",
    )


EMAIL_DEV = {
    "BACKEND": "django.core.mail.backends.console.EmailBackend",
    "HOST": "localhost",
    "PORT": 1025,
    "USE_TLS": False,
    "USE_SSL": False,
    "HOST_USER": "",
    "HOST_PASSWORD": "",
}

EMAIL_TEST = {
    "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    "HOST": "localhost",
    "PORT": 1025,
    "USE_TLS": False,
    "USE_SSL": False,
    "HOST_USER": "",
    "HOST_PASSWORD": "",
}

EMAIL_PROD = {
    "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    "HOST": EMAIL_HOST,
    "PORT": EMAIL_PORT,
    "USE_TLS": EMAIL_USE_TLS,
    "USE_SSL": EMAIL_USE_SSL,
    "HOST_USER": EMAIL_HOST_USER,
    "HOST_PASSWORD": EMAIL_HOST_PASSWORD,
}
