from celery import shared_task
import traceback
from django.core.mail import EmailMultiAlternatives, send_mail, get_connection
from django.conf import settings
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, ReplyTo
import sys
import python_http_client.exceptions

logger = logging.getLogger(__name__)


def send_sendgrid_email(
    to_emails,
    subject,
    text_content=None,
    html_content=None,
    from_email=None,
    reply_to=None,
):
    """
    Send an email using SendGrid's API with HTML and text fallback.

    This function attempts to send an HTML email first. If that fails, it falls back
    to sending a plain text email. This ensures maximum deliverability while still
    providing rich content when possible.
    """
    if isinstance(to_emails, str):
        to_emails = [to_emails]

    if text_content is not None:
        text_content = str(text_content)
    if html_content is not None:
        html_content = str(html_content)
    if subject is not None:
        subject = str(subject)

    is_test_environment = "pytest" in sys.modules or (
        getattr(settings, "TEST_RUNNER", None) is not None and "test" in sys.argv
    )

    if is_test_environment:
        from_email_str = from_email or settings.DEFAULT_FROM_EMAIL

        from django.core import mail

        if not hasattr(mail, "outbox"):
            mail.outbox = []

        if html_content:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content or "",
                from_email=from_email_str,
                to=to_emails,
                reply_to=[reply_to] if reply_to else None,
            )
            email.attach_alternative(html_content, "text/html")
            mail.outbox.append(email)
        else:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content or "",
                from_email=from_email_str,
                to=to_emails,
                reply_to=[reply_to] if reply_to else None,
            )
            mail.outbox.append(email)

        return 202

    if not text_content and not html_content:
        raise ValueError("Either text_content or html_content must be provided")

    message = Mail(
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to_emails=[To(email) for email in to_emails],
        subject=subject,
    )

    if text_content:
        message.add_content(Content("text/plain", text_content))

    if reply_to:
        message.reply_to = ReplyTo(reply_to)

    try:
        if html_content:
            try:
                html_message = Mail(
                    from_email=from_email or settings.DEFAULT_FROM_EMAIL,
                    to_emails=[To(email) for email in to_emails],
                    subject=subject,
                )

                if text_content:
                    html_message.add_content(Content("text/plain", text_content))

                html_message.add_content(Content("text/html", html_content))

                if reply_to:
                    html_message.reply_to = ReplyTo(reply_to)

                sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
                response = sg.send(html_message)

                if response.status_code not in [200, 201, 202]:
                    logger.warning(
                        f"HTML email failed with status code {response.status_code}, falling back to plain text"
                    )
                    raise Exception(
                        f"SendGrid API returned status code {response.status_code}"
                    )

                logger.info(f"Successfully sent HTML email to {to_emails}")
                return response.status_code

            except (
                python_http_client.exceptions.ForbiddenError,
                python_http_client.exceptions.BadRequestsError,
                python_http_client.exceptions.UnauthorizedError,
            ) as e:
                logger.warning(
                    f"HTML email failed with error: {str(e)}, falling back to plain text"
                )

            except Exception as e:
                logger.warning(
                    f"HTML email failed with error: {str(e)}, falling back to plain text"
                )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code not in [200, 201, 202]:
            logger.error(
                f"Failed to send plain text email. Status code: {response.status_code}"
            )
            raise Exception(f"SendGrid API returned status code {response.status_code}")

        logger.info(f"Successfully sent plain text email to {to_emails}")
        return response.status_code

    except python_http_client.exceptions.UnauthorizedError as e:
        logger.error(
            f"SendGrid unauthorized error (likely insufficient credits): {str(e)}"
        )
        raise
    except (
        python_http_client.exceptions.ForbiddenError,
        python_http_client.exceptions.BadRequestsError,
        python_http_client.exceptions.TooManyRequestsError,
    ) as e:
        logger.error(f"SendGrid API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise


def get_email_backend():
    """Get the configured email backend instance"""
    return get_connection()


def fallback_send_email(
    subject, text_content, from_email, to_email, html_content=None, reply_to=None
):
    """
    Fallback to Django's default email backend if SendGrid fails.

    This provides an additional layer of fallback beyond the HTML-to-text fallback.
    """
    try:
        send_sendgrid_email(
            to_email, subject, text_content, html_content, from_email, reply_to
        )
    except Exception as e:
        logger.error(f"SendGrid email failed, using Django's send_mail: {e}")
        try:
            if html_content:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=from_email,
                    to=[to_email] if isinstance(to_email, str) else to_email,
                    reply_to=[reply_to] if reply_to else None,
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)
            else:
                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=from_email,
                    recipient_list=(
                        [to_email] if isinstance(to_email, str) else to_email
                    ),
                    fail_silently=False,
                )
        except Exception as inner_e:
            logger.error(f"Django email backend also failed: {inner_e}")


@shared_task
def send_email(subject, text_content, from_email, to_email):
    """Send a plain text email"""
    send_sendgrid_email(to_email, subject, text_content, None, from_email=from_email)


@shared_task
def send_with_reply_to(subject, text_content, from_email, to_email, reply_to):
    """Send an email with a reply-to address"""
    send_sendgrid_email(
        to_email, subject, text_content, None, from_email=from_email, reply_to=reply_to
    )


@shared_task
def send_email_with_html(subject, text_content, html_content, from_email, to_email):
    """
    Send an email with HTML content and text fallback.

    This function will try to send an HTML email first, and if that fails,
    it will automatically fall back to the plain text version.
    """
    send_sendgrid_email(
        to_email, subject, text_content, html_content, from_email=from_email
    )


@shared_task
def send_activation_email(subject, text_content, to_email, html_content=None):
    """
    Send an account activation email with HTML content if available.

    This function will try to send an HTML email if html_content is provided,
    and will fall back to plain text if HTML sending fails.

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    try:
        send_sendgrid_email(
            to_email, subject, text_content, html_content, from_email=from_email
        )
        return True
    except python_http_client.exceptions.UnauthorizedError as e:
        logger.error(f"SendGrid unauthorized error for {to_email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send activation email to {to_email}: {str(e)}")
        return False
