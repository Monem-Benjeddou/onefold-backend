"""
OTP Delivery Service

This service handles the delivery of OTP codes via SMS or Email based on the 
OTP_DELIVERY_METHOD environment variable. 

When SMS is configured and fails, the service will automatically fall back to email delivery
if the user has an email address available.
When Email is configured, traditional email delivery is used.
"""

import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from typing import Optional

from core.tasks import send_activation_email
from core.tasks.sms import send_sms_task

logger = logging.getLogger(__name__)


def send_sms_neons(message: str, phone_numbers: list, otp_type: str = "login") -> bool:
    """
    Legacy function for sending SMS via Neons API.
    This function is kept for backward compatibility with existing tests.

    Args:
        message: SMS message content
        phone_numbers: List of phone numbers to send to
        otp_type: Type of OTP

    Returns:
        bool: True if SMS was sent successfully, False otherwise
    """
    try:

        if not phone_numbers:
            return False

        task_result = send_sms_task.delay(message, phone_numbers, otp_type)

        if isinstance(task_result, bool):
            if task_result:
                logger.info(f"SMS task queued for {phone_numbers}")
                return True
            else:
                logger.error(f"SMS task queueing failed for {phone_numbers}")
                return False

        if task_result is None:
            logger.error(
                f"SMS task queueing failed for {phone_numbers} - task_result is None"
            )
            return False

        try:
            task_id = task_result.id if hasattr(task_result, "id") else str(task_result)
            if not task_id:
                logger.error(
                    f"SMS task queueing failed for {phone_numbers} - no task ID"
                )
                return False

            logger.info(f"SMS task queued for {phone_numbers} (task_id: {task_id})")
            return True

        except Exception as task_error:
            logger.error(
                f"Error checking SMS task status for {phone_numbers}: {str(task_error)}"
            )
            return False

    except Exception as e:
        logger.error(f"Failed to queue SMS task for {phone_numbers}: {str(e)}")
        return False


class OTPDeliveryService:
    """
    Service for delivering OTP codes via SMS or Email based on configuration.

    When SMS delivery is configured (OTP_DELIVERY_METHOD=sms):
    - Uses Neons SMS API via Celery tasks
    - Falls back to email delivery if SMS fails and user has email

    When Email delivery is configured (OTP_DELIVERY_METHOD=email):
    - Uses traditional Django email backend
    """

    def __init__(self, user):
        """
        Initialize the OTP delivery service for a specific user.

        Args:
            user: User instance for whom to deliver OTPs
        """
        self.user = user

    def send_otp(self, otp_code: str, method: str = "sms") -> bool:
        """
        Instance method to send OTP using the specified method.

        Args:
            otp_code: The OTP code to send
            method: Delivery method ("sms", "email", or "both")

        Returns:
            bool: True if successfully sent, False otherwise
        """
        if method == "both":

            sms_success = self._send_otp_via_sms(self.user, otp_code, "login")
            email_success = self._send_otp_via_email(self.user, otp_code, "login")
            return sms_success or email_success
        elif method == "email":
            return self._send_otp_via_email(self.user, otp_code, "login")
        else:
            return self._send_otp_via_sms(self.user, otp_code, "login")

    def send_otp_with_fallback(self, otp_code: str) -> bool:
        """
        Send OTP with automatic fallback from SMS to email.

        Args:
            otp_code: The OTP code to send

        Returns:
            bool: True if successfully sent via any method
        """

        if self.user.phone_number:
            sms_success = self._send_otp_via_sms(self.user, otp_code, "login")
            if sms_success:
                return True

        if self.user.email:
            return self._send_otp_via_email(self.user, otp_code, "login")

        return False

    @staticmethod
    def get_delivery_method() -> str:
        """
        Get the configured OTP delivery method from Django settings.

        Returns:
            str: The delivery method from settings, defaults to "sms"
        """
        method = getattr(settings, "OTP_DELIVERY_METHOD", "email")

        if method == "" or method is None:
            return "email"

        if not isinstance(method, str):
            return "sms"

        method = method.lower().strip()

        return method

    @staticmethod
    def send_otp(user, otp_code: str, otp_type: str = "login") -> bool:
        """
        Send OTP to user via the configured delivery method (SMS or Email).

        When SMS is configured and fails, automatically falls back to email if available.

        Args:
            user: User instance
            otp_code: 6-digit OTP code
            otp_type: Type of OTP ("login", "password_reset", "verification")

        Returns:
            bool: True if sent successfully via any method, False otherwise
        """

        if not user:
            logger.error("Cannot send OTP: user is None")
            return False

        if not otp_code or len(otp_code) != 6 or not otp_code.isdigit():
            logger.error(f"Invalid OTP code format: {otp_code}")
            return False

        if otp_type not in ["login", "password_reset", "verification", "registration"]:
            logger.warning(f"Unknown OTP type: {otp_type}, defaulting to login")
            otp_type = "login"

        delivery_method = OTPDeliveryService.get_delivery_method()

        if delivery_method == "email":
            return OTPDeliveryService._send_otp_via_email(user, otp_code, otp_type)
        elif delivery_method == "sms":

            sms_fallback_enabled = getattr(settings, "SMS_FALLBACK_TO_EMAIL", True)

            if not user.phone_number:
                if sms_fallback_enabled and user.email:
                    logger.error(
                        f"User {user.email} has no phone number for SMS OTP delivery, attempting email fallback"
                    )
                    return OTPDeliveryService._send_otp_via_email(
                        user, otp_code, otp_type
                    )
                else:
                    logger.error(
                        f"User {getattr(user, 'email', 'unknown')} has no phone number for SMS OTP delivery and fallback is disabled"
                    )
                    return False

            sms_success = OTPDeliveryService._send_otp_via_sms(user, otp_code, otp_type)

            if sms_success:
                return True

            if sms_fallback_enabled and user.email:
                logger.info(
                    f"SMS delivery failed for {user.email}, falling back to email"
                )
                return OTPDeliveryService._send_otp_via_email(user, otp_code, otp_type)
            else:
                logger.error(
                    f"SMS delivery failed for user {getattr(user, 'username', 'unknown')} and no email available for fallback or fallback is disabled"
                )
                return False
        else:
            logger.warning(
                f"Unknown delivery method: {delivery_method}, defaulting to email"
            )
            return OTPDeliveryService._send_otp_via_email(user, otp_code, otp_type)

    @staticmethod
    def _send_otp_via_sms(user, otp_code: str, otp_type: str) -> bool:
        """
        Send OTP via SMS using Neons SMS API with Celery task.

        This method attempts SMS delivery and returns False if it fails,
        allowing the main send_otp method to handle fallback logic.

        Args:
            user: User instance
            otp_code: 6-digit OTP code
            otp_type: Type of OTP

        Returns:
            bool: True if SMS sent successfully, False if failed
        """
        if not user.phone_number:
            logger.warning(
                f"User {user.email} has no phone number for SMS OTP delivery"
            )
            return False

        phone_number = user.phone_number.strip()
        if not phone_number.startswith("+"):

            phone_number = "+" + phone_number.lstrip("0")

        digits_only = "".join(filter(str.isdigit, phone_number))
        if len(digits_only) < 5:
            logger.warning(
                f"Invalid phone number format for user {user.email}: {user.phone_number}"
            )
            return False

        if otp_type == "password_reset":
            message = _(
                "Your Kolct password reset OTP code is: {}. This code will expire in 10 minutes."
            ).format(otp_code)
        elif otp_type == "verification":
            message = _(
                "Your Kolct verification OTP code is: {}. This code will expire in 10 minutes."
            ).format(otp_code)
        elif otp_type == "registration":
            message = _(
                "Welcome to Kolct! Your registration OTP code is: {}. This code will expire in 10 minutes."
            ).format(otp_code)
        else:
            message = _(
                "Your Kolct login OTP code is: {}. This code will expire in 10 minutes."
            ).format(otp_code)

        try:

            task_result = send_sms_task.delay(str(message), [phone_number], otp_type)

            if isinstance(task_result, bool):
                if task_result:
                    logger.info(
                        f"OTP SMS task queued for {phone_number} (user: {user.email})"
                    )
                    return True
                else:
                    logger.error(f"SMS task queueing failed for {phone_number}")
                    return False

            if task_result is None:
                logger.error(
                    f"SMS task queueing failed for {phone_number} - task_result is None"
                )
                return False

            try:

                task_id = (
                    task_result.id if hasattr(task_result, "id") else str(task_result)
                )
                if not task_id:
                    logger.error(
                        f"SMS task queueing failed for {phone_number} - no task ID"
                    )
                    return False

                logger.info(
                    f"OTP SMS task queued successfully for {phone_number} (user: {user.email}, task_id: {task_id})"
                )
                return True

            except Exception as task_error:
                logger.error(
                    f"Error checking SMS task status for {phone_number}: {str(task_error)}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to queue SMS task for {phone_number}: {str(e)}")
            return False

    @staticmethod
    def _send_otp_via_email(user, otp_code: str, otp_type: str) -> bool:
        """
        Send OTP via email (fallback method).

        Args:
            user: User instance
            otp_code: 6-digit OTP code
            otp_type: Type of OTP

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not user.email:
            logger.error(
                f"User {getattr(user, 'username', 'unknown')} has no email address for email OTP delivery"
            )
            return False

        try:
            if otp_type == "password_reset":
                subject = _("Password Reset OTP Code")
                text_content = _(
                    f"Your password reset OTP code is: {otp_code}. This code will expire in 10 minutes."
                )
                html_content = render_to_string(
                    "auth/emails/password_reset_otp.html",
                    {"code": otp_code, "user": user},
                )
            elif otp_type == "verification":
                subject = _("Email Verification OTP Code")
                text_content = _(f"Your verification OTP code is: {otp_code}")
                html_content = render_to_string(
                    "auth/emails/verification_code.html",
                    {"code": otp_code, "user": user},
                )
            elif otp_type == "registration":
                subject = _("Welcome to Kolct - Verify Your Account")
                text_content = _(
                    f"Welcome to Kolct! Your registration verification code is: {otp_code}. This code will expire in 10 minutes."
                )
                html_content = render_to_string(
                    "auth/emails/verification_code.html",
                    {"code": otp_code, "user": user},
                )
            else:
                subject = _("Your Login OTP Code")
                text_content = _(f"Your OTP code is: {otp_code}")
                html_content = render_to_string(
                    "auth/emails/otp_code.html", {"code": otp_code, "user": user}
                )

            send_activation_email.delay(
                subject=str(subject),
                text_content=str(text_content),
                html_content=html_content,
                to_email=user.email,
            )

            logger.info(f"OTP sent via email to {user.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send OTP email to {user.email}: {str(e)}")
            return False

    @staticmethod
    def validate_user_for_otp_delivery(user) -> tuple[bool, Optional[str]]:
        """
        Validate that user has the required contact information for OTP delivery.

        Args:
            user: User instance

        Returns:
            tuple: (is_valid, error_message)
        """
        delivery_method = OTPDeliveryService.get_delivery_method()

        if delivery_method == "sms":
            sms_fallback_enabled = getattr(settings, "SMS_FALLBACK_TO_EMAIL", True)

            if not user.phone_number:

                if sms_fallback_enabled and user.email:
                    return True, None
                else:
                    return False, _("Phone number is required for SMS OTP delivery.")
        elif delivery_method == "email":
            if not user.email:
                return False, _("Email address is required for email OTP delivery.")
        else:

            sms_fallback_enabled = getattr(settings, "SMS_FALLBACK_TO_EMAIL", True)

            if not user.phone_number:
                if sms_fallback_enabled and user.email:
                    return True, None
                else:
                    return False, _("Phone number is required for SMS OTP delivery.")

        return True, None

    @staticmethod
    def send_sms_otp(user, otp_code: str, otp_type: str = "verification") -> bool:
        """
        Send OTP directly via SMS without checking global delivery method settings.

        Args:
            user: User instance
            otp_code: 6-digit OTP code
            otp_type: Type of OTP ("login", "password_reset", "verification")

        Returns:
            bool: True if SMS sent successfully, False otherwise
        """
        return OTPDeliveryService._send_otp_via_sms(user, otp_code, otp_type)

    @staticmethod
    def send_email_otp(user, otp_code: str, otp_type: str = "verification") -> bool:
        """
        Send OTP directly via email without checking global delivery method settings.

        Args:
            user: User instance
            otp_code: 6-digit OTP code
            otp_type: Type of OTP ("login", "password_reset", "verification")

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        return OTPDeliveryService._send_otp_via_email(user, otp_code, otp_type)

    @staticmethod
    def get_delivery_target_display(user) -> str:
        """
        Get a display-friendly string showing where the OTP was sent.

        With fallback logic, this shows the primary method attempted,
        though actual delivery may fall back to email if SMS fails.

        Args:
            user: User instance

        Returns:
            str: Display string like "SMS to +1234***5678" or "email to u***@example.com"
        """
        delivery_method = OTPDeliveryService.get_delivery_method()
        sms_fallback_enabled = getattr(settings, "SMS_FALLBACK_TO_EMAIL", True)

        if delivery_method == "email":
            if user.email:
                email = user.email
                parts = email.split("@")
                if len(parts) == 2:
                    username, domain = parts
                    if len(username) > 2:

                        masked_username = (
                            username[:2] + "*" * (len(username) - 3) + username[-1:]
                        )
                    else:
                        masked_username = "*" * len(username)
                    masked_email = f"{masked_username}@{domain}"
                else:
                    masked_email = "*" * len(email)
                return _("email to {}").format(masked_email)
            else:
                return _("email (not available)")
        else:

            if user.phone_number:
                phone = user.phone_number
                if len(phone) > 4:
                    masked_phone = phone[:4] + "*" * (len(phone) - 8) + phone[-4:]
                else:
                    masked_phone = "*" * len(phone)

                if sms_fallback_enabled and user.email:
                    fallback_note = " (with email fallback)"
                else:
                    fallback_note = ""

                return _("SMS to {}{}").format(masked_phone, fallback_note)
            else:

                if sms_fallback_enabled and user.email:
                    email = user.email
                    parts = email.split("@")
                    if len(parts) == 2:
                        username, domain = parts
                        if len(username) > 2:
                            masked_username = (
                                username[:2] + "*" * (len(username) - 3) + username[-1:]
                            )
                        else:
                            masked_username = "*" * len(username)
                        masked_email = f"{masked_username}@{domain}"
                    else:
                        masked_email = "*" * len(email)
                    return _("email to {} (SMS fallback)").format(masked_email)
                else:
                    return _("SMS (not available)")
