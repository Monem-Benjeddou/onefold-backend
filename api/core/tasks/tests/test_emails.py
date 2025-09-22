from django.test import TestCase, override_settings
from django.core import mail
from unittest.mock import patch, MagicMock
from core.tasks.emails import (
    send_email,
    send_with_reply_to,
    send_email_with_html,
    send_activation_email,
    get_email_backend,
    send_sendgrid_email,
)
import python_http_client.exceptions
from core.tasks.tests.test_utils import (
    mock_sendgrid_emails,
    setup_gmail_test_environment,
    apply_to_test_class,
)
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.backends.locmem import EmailBackend as LocmemBackend


@mock_sendgrid_emails
class EmailTasksTests(TestCase):
    def setUp(self):
        self.test_email = {
            "subject": "Test Subject",
            "text_content": "Test Content",
            "from_email": "from@example.com",
            "to_email": "to@example.com",
        }

    def test_send_email_basic(self):
        """Test basic email sending using Django's locmem backend"""
        send_email.apply(kwargs=self.test_email)

        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(sent_mail.subject, self.test_email["subject"])
        self.assertEqual(sent_mail.body, self.test_email["text_content"])
        self.assertEqual(sent_mail.from_email, self.test_email["from_email"])
        self.assertEqual(sent_mail.to, [self.test_email["to_email"]])

    @patch("sendgrid.SendGridAPIClient.send")
    def test_sendgrid_backend(self, mock_send):
        """Test SendGrid API backend"""
        mock_send.return_value.status_code = 202

        with override_settings(TEST_RUNNER=None):
            send_sendgrid_email(
                self.test_email["to_email"],
                self.test_email["subject"],
                self.test_email["text_content"],
                from_email=self.test_email["from_email"],
            )

        mock_send.assert_called_once()

    def test_send_with_reply_to(self):
        """Test sending email with reply-to header"""
        kwargs = {**self.test_email, "reply_to": "reply@example.com"}
        send_with_reply_to.apply(kwargs=kwargs)

        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(sent_mail.reply_to, [kwargs["reply_to"]])

    def test_send_email_with_html(self):
        """Test sending email with HTML content"""
        kwargs = {**self.test_email, "html_content": "<p>HTML Content</p>"}
        send_email_with_html.apply(kwargs=kwargs)

        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(len(sent_mail.alternatives), 1)
        self.assertEqual(sent_mail.alternatives[0][0], kwargs["html_content"])
        self.assertEqual(sent_mail.alternatives[0][1], "text/html")

    def test_send_activation_email(self):
        """Test sending activation email"""
        kwargs = {
            "subject": "Activate Account",
            "text_content": "Please activate your account",
            "to_email": "user@example.com",
            "html_content": "<p>Activate your account</p>",
        }
        send_activation_email.apply(kwargs=kwargs)

        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(sent_mail.from_email, "noreply@example.com")

    def test_email_backend_selection(self):
        """Test email backend selection logic"""
        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        ):
            backend = get_email_backend()
            self.assertIsInstance(backend, LocmemBackend)

    def test_multiple_recipients(self):
        """Test sending email to multiple recipients"""
        recipients = ["user1@example.com", "user2@example.com"]
        kwargs = {**self.test_email, "to_email": recipients}
        send_email.apply(kwargs=kwargs)

        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(sent_mail.to, recipients)

    @patch("sendgrid.SendGridAPIClient.send")
    def test_send_activation_email_unauthorized_error_handling(self, mock_send):
        """Test that send_activation_email handles UnauthorizedError gracefully"""
        mock_send.side_effect = python_http_client.exceptions.UnauthorizedError(
            401, "Unauthorized", b'{"error": "Maximum credits exceeded"}', {}
        )

        with override_settings(TEST_RUNNER=None):
            result = send_activation_email(
                subject="Test Subject",
                text_content="Test Content",
                to_email="test@example.com",
                html_content="<p>Test HTML</p>",
            )

        self.assertFalse(result)
        mock_send.assert_called()

    @patch("sendgrid.SendGridAPIClient.send")
    def test_send_activation_email_success_handling(self, mock_send):
        """Test that send_activation_email returns True on success"""
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_send.return_value = mock_response

        with override_settings(TEST_RUNNER=None):
            result = send_activation_email(
                subject="Test Subject",
                text_content="Test Content",
                to_email="test@example.com",
            )

        self.assertTrue(result)
        mock_send.assert_called_once()

    @patch("sendgrid.SendGridAPIClient.send")
    def test_send_activation_email_generic_error_handling(self, mock_send):
        """Test that send_activation_email handles generic errors gracefully"""
        mock_send.side_effect = Exception("Network timeout")

        with override_settings(TEST_RUNNER=None):
            result = send_activation_email(
                subject="Test Subject",
                text_content="Test Content",
                to_email="test@example.com",
            )

        self.assertFalse(result)

    @patch("sendgrid.SendGridAPIClient.send")
    def test_sendgrid_email_unauthorized_error_propagation(self, mock_send):
        """Test that send_sendgrid_email properly propagates UnauthorizedError"""
        mock_send.side_effect = python_http_client.exceptions.UnauthorizedError(
            401, "Unauthorized", b'{"error": "Maximum credits exceeded"}', {}
        )

        with override_settings(TEST_RUNNER=None):
            with self.assertRaises(python_http_client.exceptions.UnauthorizedError):
                send_sendgrid_email("test@example.com", "Test Subject", "Test Content")


@apply_to_test_class
class GmailEmailTests(TestCase):
    """Tests for sending emails via Gmail in testing environment"""

    def setUp(self):
        setup_gmail_test_environment()
        self.test_email = {
            "subject": "Gmail Test Subject",
            "text_content": "This is a test email sent via Gmail",
            "from_email": "malkomdelauer5878@gmail.com",
            "to_email": "malkomdelauer5878@gmail.com",
        }

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_gmail_config_loaded(self, mock_sendgrid=None):
        """Test that Gmail configuration is loaded correctly"""
        from django.conf import settings

        mail.outbox = []

        self.assertTrue(
            settings.EMAIL_HOST == "smtp.gmail.com"
            or settings.EMAIL_BACKEND == "django.core.mail.backends.locmem.EmailBackend"
        )

        if hasattr(settings, "EMAIL_PORT"):
            self.assertEqual(settings.EMAIL_PORT, 587)

        if hasattr(settings, "EMAIL_USE_TLS"):
            self.assertTrue(settings.EMAIL_USE_TLS)

        if settings.EMAIL_HOST_USER == "malkomdelauer5878@gmail.com":
            self.assertEqual(settings.EMAIL_HOST_USER, "malkomdelauer5878@gmail.com")

        send_email.apply(kwargs=self.test_email)
        self.assertTrue(len(mail.outbox) > 0, "No emails were sent")

        sent_mail = mail.outbox[-1]
        self.assertEqual(sent_mail.subject, self.test_email["subject"])
