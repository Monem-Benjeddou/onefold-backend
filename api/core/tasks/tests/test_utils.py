import functools
from unittest.mock import patch
from django.conf import settings
from django.test import override_settings
from django.core import mail
import inspect


def mock_sendgrid_emails(func):
    """
    Decorator to mock SendGrid API calls and populate Django's mail.outbox.
    This ensures that emails sent during tests are captured in mail.outbox
    and no actual API calls are made to SendGrid.
    """

    @functools.wraps(func)
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        SENDGRID_API_KEY="mock-api-key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        EMAIL_ACTIVATION_HOST="noreply@example.com",
        TEST_RUNNER="django.test.runner.DiscoverRunner",
    )
    @patch("sendgrid.SendGridAPIClient")
    def wrapper(*args, **kwargs):
        mail.outbox = []

        mock_sg = args[1] if len(args) > 1 else None
        if mock_sg:
            mock_sg.return_value.send.return_value.status_code = 202

        sig = inspect.signature(func)
        if len(sig.parameters) == 1:
            return func(args[0])
        else:
            return func(*args, **kwargs)

    return wrapper


def setup_test_email_environment():
    """
    Setup the test environment for email testing.
    This function can be called in setUp methods of test classes.
    """

    mail.outbox = []

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.SENDGRID_API_KEY = "mock-api-key"
    settings.DEFAULT_FROM_EMAIL = "noreply@example.com"
    settings.EMAIL_ACTIVATION_HOST = "noreply@example.com"
    settings.TEST_RUNNER = "django.test.runner.DiscoverRunner"


def setup_gmail_test_environment():
    """
    Setup the Gmail test environment for integration testing.
    This function can be called when you want to actually send emails via Gmail.
    """

    mail.outbox = []

    settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    settings.EMAIL_HOST = "smtp.gmail.com"
    settings.EMAIL_PORT = 587
    settings.EMAIL_USE_TLS = True
    settings.EMAIL_HOST_USER = "malkomdelauer5878@gmail.com"
    settings.EMAIL_HOST_PASSWORD = "nvzvdwdwdwdrtrfzmw"
    settings.DEFAULT_FROM_EMAIL = "malkomdelauer5878@gmail.com"
    settings.EMAIL_ACTIVATION_HOST = "malkomdelauer5878@gmail.com"
    settings.TEST_RUNNER = "django.test.runner.DiscoverRunner"


def apply_to_test_class(cls):
    """
    Apply the mock_sendgrid_emails decorator to all test methods in a class.
    This is a utility function to easily apply the decorator to all test methods.

    Usage:
        @apply_to_test_class
        class MyTestClass(TestCase):
            def test_method1(self):
                ...
    """
    for attr_name in dir(cls):
        if attr_name.startswith("test_"):
            attr = getattr(cls, attr_name)
            if callable(attr):
                setattr(cls, attr_name, mock_sendgrid_emails(attr))
    return cls
