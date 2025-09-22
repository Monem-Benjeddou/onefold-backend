"""
Email settings for the project.
"""

from ..config_loader import get_email_config


email_config = get_email_config()


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


EMAIL_HOST = email_config["HOST"]
EMAIL_PORT = email_config["PORT"]
EMAIL_USE_TLS = email_config["USE_TLS"]
EMAIL_USE_SSL = email_config["USE_SSL"]
EMAIL_HOST_USER = email_config["HOST_USER"]
EMAIL_HOST_PASSWORD = email_config["HOST_PASSWORD"]
DEFAULT_FROM_EMAIL = email_config["DEFAULT_FROM"]
SERVER_EMAIL = email_config["DEFAULT_FROM"]

EMAIL_ACTIVATION_HOST = email_config["ACTIVATION_HOST"]
EMAIL_ACTIVATION_PASSWORD = email_config["ACTIVATION_PASSWORD"]
EMAIL_ACTIVATION_PORT = email_config["ACTIVATION_PORT"]
EMAIL_ACTIVATION_USE_TLS = email_config["ACTIVATION_USE_TLS"]
EMAIL_ACTIVATION_USE_SSL = email_config["ACTIVATION_USE_SSL"]

EMAIL_NO_REPLY_PORT = email_config["NO_REPLY_PORT"]

EMAIL_TIMEOUT = 30

ADMINS = [
    ("Admin", email_config["DEFAULT_FROM"]),
]

MANAGERS = ADMINS

EMAIL_TEST = "test@example.com"


def get_email_activation_backend():
    from django.core.mail.backends.smtp import EmailBackend

    return EmailBackend(
        host=EMAIL_HOST,
        port=int(email_config["ACTIVATION_PORT"]),
        username=EMAIL_ACTIVATION_HOST,
        password=EMAIL_ACTIVATION_PASSWORD,
        use_tls=email_config["ACTIVATION_USE_TLS"] == "True",
        use_ssl=email_config["ACTIVATION_USE_SSL"] == "True",
    )


def get_email_no_reply_backend():
    from django.core.mail.backends.smtp import EmailBackend

    return EmailBackend(
        host=EMAIL_HOST,
        port=int(email_config["NO_REPLY_PORT"]),
        username=EMAIL_HOST_USER,
        password=EMAIL_HOST_PASSWORD,
        use_tls=email_config["NO_REPLY_USE_TLS"] == "True",
        use_ssl=email_config["NO_REPLY_USE_SSL"] == "True",
    )


SENDGRID_API_KEY = email_config.get("SENDGRID_API_KEY", "")
if SENDGRID_API_KEY:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

    EMAIL_HOST = "smtp.sendgrid.net"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = "apikey"
    EMAIL_HOST_PASSWORD = SENDGRID_API_KEY

    SENDGRID_SANDBOX_MODE_IN_DEBUG = (
        email_config.get("SENDGRID_SANDBOX_MODE_IN_DEBUG", "False") == "True"
    )
    SENDGRID_ECHO_TO_STDOUT = (
        email_config.get("SENDGRID_ECHO_TO_STDOUT", "False") == "True"
    )

    sendgrid_sender = email_config.get("SENDGRID_SENDER", "")
    if sendgrid_sender:
        DEFAULT_FROM_EMAIL = sendgrid_sender
        SERVER_EMAIL = sendgrid_sender


try:
    ANYMAIL = {
        "MAILGUN_API_KEY": email_config.get("MAILGUN_API_KEY", ""),
        "MAILGUN_SENDER_DOMAIN": email_config.get("MAILGUN_SENDER_DOMAIN", ""),
    }
    if (
        ANYMAIL["MAILGUN_API_KEY"]
        and ANYMAIL["MAILGUN_SENDER_DOMAIN"]
        and not SENDGRID_API_KEY
    ):
        EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
except Exception:
    pass
