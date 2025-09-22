"""
Dual-service communication manager for email and SMS routing.
Routes emails to SendGrid and SMS to appropriate SMS services.
"""

import logging
from typing import Union, List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import hashlib


from core.tasks.emails import send_sendgrid_email


from .twilio_sms_service import twilio_sms_service, CommunicationResult
from .sms_router import sms_router, SMSProvider
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


@dataclass
class CommunicationRequest:
    """Standardized communication request structure."""

    recipient: Union[str, List[str]]
    content: str
    communication_type: str
    template_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CommunicationService:
    """
    Dual-service manager for all communication channels.

    Features:
    - Routes emails to SendGrid (existing service - UNCHANGED)
    - Routes SMS to appropriate services (Neons/Twilio based on region)
    - Template management and standardization
    - Delivery tracking and logging
    - Performance monitoring
    - Fallback and error handling
    """

    def __init__(self):

        self.twilio_sms_service = twilio_sms_service
        self.sms_router = sms_router

        self.performance_cache_ttl = 3600

    def send_email(
        self,
        to_emails: Union[str, List[str]],
        subject: str,
        text_content: Optional[str] = None,
        html_content: Optional[str] = None,
        template_type: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        **kwargs,
    ) -> CommunicationResult:
        """
        Send email via SendGrid (EXISTING SERVICE - NO CHANGES).

        Args:
            to_emails: Recipient email address(es)
            subject: Email subject
            text_content: Plain text content
            html_content: HTML content
            template_type: Email template identifier
            from_email: Sender email address
            reply_to: Reply-to address
            **kwargs: Additional email parameters

        Returns:
            CommunicationResult with delivery status
        """
        import time

        start_time = time.time()

        if template_type:
            text_content, html_content, subject = self._apply_email_template(
                template_type, text_content, html_content, subject, **kwargs
            )

        try:

            status_code = send_sendgrid_email(
                to_emails=to_emails,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=from_email,
                reply_to=reply_to,
            )

            response_time = time.time() - start_time

            result = CommunicationResult(
                success=status_code in [200, 201, 202],
                service_used="sendgrid",
                response_time=response_time,
                status_code=status_code,
            )

        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            result = CommunicationResult(
                success=False,
                error=str(e),
                service_used="sendgrid",
                response_time=time.time() - start_time,
            )

        self._track_communication_performance("email", result)

        self._log_communication_attempt("email", to_emails, result, template_type)

        return result

    def send_sms(
        self,
        phone_number: str,
        message: str,
        template_type: Optional[str] = None,
        force_provider: Optional[str] = None,
        **kwargs,
    ) -> CommunicationResult:
        """
        Send SMS via intelligent routing with template support.

        Args:
            phone_number: Recipient phone number
            message: SMS message content
            template_type: SMS template identifier
            force_provider: Override routing ('neons' or 'twilio')
            **kwargs: Additional SMS parameters

        Returns:
            CommunicationResult with delivery status
        """

        if template_type:
            message = self._apply_sms_template(template_type, message, **kwargs)

        provider_enum = None
        if force_provider:
            try:
                provider_enum = SMSProvider(force_provider.lower())
            except ValueError:
                logger.warning(
                    f"Invalid force_provider '{force_provider}', using routing"
                )

        result = self.sms_router.send_sms(
            phone_number=phone_number,
            message=message,
            force_provider=provider_enum,
            **kwargs,
        )

        self._track_communication_performance("sms", result)

        self._log_communication_attempt("sms", phone_number, result, template_type)

        return result

    def send_otp_email(
        self, email: str, otp_code: str, otp_type: str = "login", **kwargs
    ) -> CommunicationResult:
        """Send OTP via email using standardized templates (via SendGrid)."""
        templates = {
            "login": {
                "subject": "Your Kolct Login Code",
                "template": "Your Kolct login code is: {}. Valid for 10 minutes.",
            },
            "registration": {
                "subject": "Welcome to Kolct - Verify Your Account",
                "template": "Welcome to Kolct! Your verification code is: {}. Valid for 10 minutes.",
            },
            "password_reset": {
                "subject": "Reset Your Kolct Password",
                "template": "Your Kolct password reset code is: {}. Valid for 10 minutes.",
            },
        }

        template_data = templates.get(otp_type, templates["login"])
        message = template_data["template"].format(otp_code)

        return self.send_email(
            to_emails=email,
            subject=template_data["subject"],
            text_content=message,
            template_type=f"otp_{otp_type}",
            otp_code=otp_code,
            **kwargs,
        )

    def send_otp_sms(
        self, phone_number: str, otp_code: str, otp_type: str = "login", **kwargs
    ) -> CommunicationResult:
        """Send OTP via SMS using intelligent routing."""
        return self.sms_router.send_otp_sms(
            phone_number=phone_number, otp_code=otp_code, otp_type=otp_type, **kwargs
        )

    def send_dual_otp(
        self,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        otp_code: str = None,
        otp_type: str = "login",
        **kwargs,
    ) -> Dict[str, CommunicationResult]:
        """
        Send OTP via both email (SendGrid) and SMS (Twilio/Neons) channels.

        Returns:
            Dict with 'email' and 'sms' communication results
        """
        results = {}

        if email:
            results["email"] = self.send_otp_email(email, otp_code, otp_type, **kwargs)

        if phone_number:
            results["sms"] = self.send_otp_sms(
                phone_number, otp_code, otp_type, **kwargs
            )

        return results

    def _apply_email_template(
        self,
        template_type: str,
        text_content: str,
        html_content: str,
        subject: str,
        **kwargs,
    ) -> tuple:
        """Apply email template transformations."""

        if template_type and template_type.startswith("otp_"):

            otp_code = kwargs.get("otp_code", "XXXXXX")
            if text_content and "{}" in text_content:
                text_content = text_content.format(otp_code)
            if html_content and "{}" in html_content:
                html_content = html_content.format(otp_code)

        return text_content, html_content, subject

    def _apply_sms_template(self, template_type: str, message: str, **kwargs) -> str:
        """Apply SMS template transformations."""
        if template_type and template_type.startswith("otp_"):
            otp_code = kwargs.get("otp_code", "XXXXXX")
            if "{}" in message:
                message = message.format(otp_code)

        return message

    def _track_communication_performance(
        self, communication_type: str, result: CommunicationResult
    ):
        """Track communication performance metrics."""
        cache_key = f"comm_performance:{communication_type}"

        success_key = f"{cache_key}:success"
        failure_key = f"{cache_key}:failure"
        response_time_key = f"{cache_key}:avg_response_time"

        if result.success:
            cache.set(
                success_key, cache.get(success_key, 0) + 1, self.performance_cache_ttl
            )
        else:
            cache.set(
                failure_key, cache.get(failure_key, 0) + 1, self.performance_cache_ttl
            )

        if result.response_time > 0:
            current_avg = cache.get(response_time_key, 0)
            success_count = cache.get(success_key, 0)
            failure_count = cache.get(failure_key, 0)
            total_requests = success_count + failure_count

            if total_requests > 0:
                new_avg = (
                    (current_avg * (total_requests - 1)) + result.response_time
                ) / total_requests
                cache.set(response_time_key, new_avg, self.performance_cache_ttl)

    def _log_communication_attempt(
        self,
        communication_type: str,
        recipient: Union[str, List[str]],
        result: CommunicationResult,
        template_type: Optional[str] = None,
    ):
        """Log communication attempt for audit and debugging."""

        if isinstance(recipient, str):
            if "@" in recipient:

                local, domain = recipient.split("@")
                recipient_log = f"***@{domain}"
            else:

                recipient_log = f"***{recipient[-4:]}" if len(recipient) > 4 else "***"
        else:
            recipient_log = f"{len(recipient)} recipients"

        log_data = {
            "type": communication_type,
            "recipient": recipient_log,
            "success": result.success,
            "service": result.service_used,
            "template": template_type,
            "response_time": result.response_time,
            "retry_count": result.retry_count,
        }

        if result.success:
            logger.info(
                f"Communication sent successfully to {recipient_log}", extra=log_data
            )
        else:
            log_data["error"] = result.error
            logger.error(f"Communication failed to {recipient_log}", extra=log_data)

    def get_service_health(self) -> Dict[str, Any]:
        """Get comprehensive health status of all communication services."""
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {},
        }

        try:

            sendgrid_configured = bool(getattr(settings, "SENDGRID_API_KEY", None))
            health_status["services"]["sendgrid_email"] = {
                "status": "healthy" if sendgrid_configured else "disabled",
                "configured": sendgrid_configured,
                "message": "SendGrid email service"
                + (" is configured" if sendgrid_configured else " not configured"),
            }

            if not sendgrid_configured:
                health_status["overall_status"] = "degraded"

        except Exception as e:
            health_status["services"]["sendgrid_email"] = {
                "status": "error",
                "error": str(e),
            }
            health_status["overall_status"] = "degraded"

        try:
            twilio_sms_health = self.twilio_sms_service.health_check()
            health_status["services"]["twilio_sms"] = twilio_sms_health

            if twilio_sms_health.get("overall_status") not in [
                "healthy",
                "degraded",
                "disabled",
            ]:
                health_status["overall_status"] = "degraded"

        except Exception as e:
            health_status["services"]["twilio_sms"] = {
                "status": "error",
                "error": str(e),
            }
            health_status["overall_status"] = "degraded"

        try:
            sms_health = self.sms_router.get_routing_status()
            health_status["services"]["sms_routing"] = sms_health

            for service_name, service_status in sms_health.get("services", {}).items():
                if service_status.get("status") == "unhealthy":
                    if health_status["overall_status"] == "healthy":
                        health_status["overall_status"] = "degraded"

        except Exception as e:
            health_status["services"]["sms_routing"] = {
                "status": "error",
                "error": str(e),
            }
            health_status["overall_status"] = "degraded"

        health_status["performance"] = self._get_performance_statistics()

        return health_status

    def _get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance statistics for all communication channels."""
        stats = {}

        for comm_type in ["email", "sms"]:
            cache_prefix = f"comm_performance:{comm_type}"

            success_count = cache.get(f"{cache_prefix}:success", 0)
            failure_count = cache.get(f"{cache_prefix}:failure", 0)
            avg_response_time = cache.get(f"{cache_prefix}:avg_response_time", 0)

            total_requests = success_count + failure_count
            success_rate = (
                (success_count / total_requests * 100) if total_requests > 0 else 0
            )

            stats[comm_type] = {
                "total_requests": total_requests,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate_percent": round(success_rate, 2),
                "avg_response_time_seconds": round(avg_response_time, 3),
            }

        return stats


communication_service = CommunicationService()
