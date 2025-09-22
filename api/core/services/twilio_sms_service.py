"""
Twilio SMS service for international SMS and OTP functionality.
NOTE: This service handles SMS only. Email remains with SendGrid.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import re
import time

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioException

    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio SDK not installed. Install with: pip install twilio")


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"


@dataclass
class CommunicationResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    service_used: Optional[str] = None
    retry_count: int = 0
    response_time: float = 0.0
    status_code: Optional[int] = None


class TwilioSMSService:
    """
    Twilio SMS service for international SMS and OTP communication.

    Features:
    - International SMS via Twilio SMS API
    - OTP verification via Twilio Verify API
    - Health monitoring and status reporting
    - Retry logic with exponential backoff
    - Comprehensive error handling

    NOTE: This service handles SMS only. Email is handled by existing SendGrid service.
    """

    def __init__(self):
        self.account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
        self.auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
        self.sms_from = getattr(settings, "TWILIO_SMS_FROM_NUMBER", None)
        self.verify_service_sid = getattr(settings, "TWILIO_VERIFY_SERVICE_SID", None)

        self.twilio_client = None
        self._initialize_client()

        self.request_timeout = getattr(settings, "TWILIO_REQUEST_TIMEOUT", 30)

    def _initialize_client(self):
        """Initialize Twilio SMS client with error handling."""
        if not TWILIO_AVAILABLE:
            logger.warning("Twilio SDK not available")
            return

        try:
            if self.account_sid and self.auth_token:
                self.twilio_client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio SMS client initialized successfully")
            else:
                logger.warning("Twilio SMS credentials not configured")

        except Exception as e:
            logger.error(f"Failed to initialize Twilio SMS client: {str(e)}")

    def is_sms_configured(self) -> bool:
        """Check if SMS service is properly configured."""
        return bool(
            self.twilio_client 
            and self.sms_from 
            and self.sms_from not in ["+1234567890", "1234567890", "+15005550006"]
        )

    def is_verify_configured(self) -> bool:
        """Check if OTP verification service is properly configured."""
        return bool(self.twilio_client and self.verify_service_sid)

    def send_sms(
        self, phone_number: str, message: str, **kwargs
    ) -> CommunicationResult:
        """
        Send SMS via Twilio SMS API - single attempt only.

        Args:
            phone_number: Recipient phone number (E.164 format)
            message: SMS message content

        Returns:
            CommunicationResult with delivery status and details
        """
        start_time = time.time()

        if not self.is_sms_configured():
            return CommunicationResult(
                success=False,
                error="SMS service not configured",
                service_used="twilio_sms",
            )

        
        if self.sms_from in ["+1234567890", "1234567890", "+15005550006"]:
            logger.error(f"Cannot send SMS: From number '{self.sms_from}' is a placeholder/test number")
            return CommunicationResult(
                success=False,
                error=f"Invalid from number: '{self.sms_from}' is not a verified Twilio phone number. Please configure TWILIO_SMS_FROM_NUMBER with a verified number from your Twilio account.",
                service_used="twilio_sms",
                response_time=time.time() - start_time,
            )

        formatted_phone = self._format_phone_number(phone_number)
        if not formatted_phone:
            return CommunicationResult(
                success=False,
                error=f"Invalid phone number format: {phone_number}",
                service_used="twilio_sms",
            )

        try:
            twilio_message = self.twilio_client.messages.create(
                body=str(message), from_=self.sms_from, to=formatted_phone
            )

            response_time = time.time() - start_time
            return CommunicationResult(
                success=True,
                message_id=twilio_message.sid,
                service_used="twilio_sms",
                response_time=response_time,
            )

        except TwilioException as e:
            error_str = str(e)
            
            
            if "21659" in error_str:
                logger.error(f"Twilio Error 21659: From number '{self.sms_from}' is not registered for messaging")
                return CommunicationResult(
                    success=False,
                    error=f"From number '{self.sms_from}' is not registered in your Twilio account. Please verify the number in Twilio console or configure a verified number.",
                    service_used="twilio_sms",
                    response_time=time.time() - start_time,
                    status_code=21659,
                )
            elif "21614" in error_str:
                logger.error(f"Twilio Error 21614: Invalid to number '{formatted_phone}'")
                return CommunicationResult(
                    success=False,
                    error=f"Invalid recipient number: {formatted_phone}",
                    service_used="twilio_sms",
                    response_time=time.time() - start_time,
                    status_code=21614,
                )
            else:
                logger.error(f"Twilio SMS failed: {error_str}")
                return CommunicationResult(
                    success=False,
                    error=error_str,
                    service_used="twilio_sms",
                    response_time=time.time() - start_time,
                )
                
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            return CommunicationResult(
                success=False,
                error=str(e),
                service_used="twilio_sms",
                response_time=time.time() - start_time,
            )

    def send_verification_code(
        self, phone_number: str, channel: str = "sms", **kwargs
    ) -> CommunicationResult:
        """
        Send verification code via Twilio Verify API.

        Args:
            phone_number: Recipient phone number (E.164 format)
            channel: Delivery channel ('sms' or 'call')

        Returns:
            CommunicationResult with delivery status
        """
        start_time = time.time()

        if not self.is_verify_configured():
            return CommunicationResult(
                success=False,
                error="Verify service not configured",
                service_used="twilio_verify",
            )

        formatted_phone = self._format_phone_number(phone_number)
        if not formatted_phone:
            return CommunicationResult(
                success=False,
                error=f"Invalid phone number format: {phone_number}",
                service_used="twilio_verify",
            )

        try:
            verification = self.twilio_client.verify.v2.services(
                self.verify_service_sid
            ).verifications.create(to=formatted_phone, channel=channel)

            response_time = time.time() - start_time

            logger.info(f"Verification code sent to {formatted_phone} via {channel}")
            return CommunicationResult(
                success=True,
                message_id=verification.sid,
                service_used="twilio_verify",
                response_time=response_time,
            )

        except TwilioException as e:
            logger.error(f"Twilio Verify failed: {str(e)}")
            return CommunicationResult(
                success=False,
                error=str(e),
                service_used="twilio_verify",
                response_time=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"Verification sending failed: {str(e)}")
            return CommunicationResult(
                success=False,
                error=str(e),
                service_used="twilio_verify",
                response_time=time.time() - start_time,
            )

    def verify_code(
        self, phone_number: str, code: str, **kwargs
    ) -> CommunicationResult:
        """
        Verify a code sent via Twilio Verify API.

        Args:
            phone_number: Phone number that received the code
            code: Verification code to check

        Returns:
            CommunicationResult with verification status
        """
        start_time = time.time()

        if not self.is_verify_configured():
            return CommunicationResult(
                success=False,
                error="Verify service not configured",
                service_used="twilio_verify",
            )

        formatted_phone = self._format_phone_number(phone_number)
        if not formatted_phone:
            return CommunicationResult(
                success=False,
                error=f"Invalid phone number format: {phone_number}",
                service_used="twilio_verify",
            )

        try:
            verification_check = self.twilio_client.verify.v2.services(
                self.verify_service_sid
            ).verification_checks.create(to=formatted_phone, code=str(code))

            response_time = time.time() - start_time

            if verification_check.status == "approved":
                logger.info(f"Verification code approved for {formatted_phone}")
                return CommunicationResult(
                    success=True,
                    message_id=verification_check.sid,
                    service_used="twilio_verify",
                    response_time=response_time,
                )
            else:
                logger.warning(
                    f"Verification code failed for {formatted_phone}: {verification_check.status}"
                )
                return CommunicationResult(
                    success=False,
                    error=f"Verification failed: {verification_check.status}",
                    service_used="twilio_verify",
                    response_time=response_time,
                )

        except TwilioException as e:
            logger.error(f"Twilio Verify check failed: {str(e)}")
            return CommunicationResult(
                success=False,
                error=str(e),
                service_used="twilio_verify",
                response_time=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"Verification check failed: {str(e)}")
            return CommunicationResult(
                success=False,
                error=str(e),
                service_used="twilio_verify",
                response_time=time.time() - start_time,
            )

    def _format_phone_number(self, phone_number: str) -> Optional[str]:
        """Format phone number to E.164 format for Twilio."""
        if not phone_number:
            return None

        clean_number = re.sub(r"[^\d+]", "", phone_number)

        if not clean_number:
            return None

        if clean_number.startswith("+"):

            digits_part = clean_number[1:]
            if (
                not digits_part.isdigit()
                or len(digits_part) < 7
                or len(digits_part) > 15
            ):
                return None
            return clean_number

        if clean_number.startswith("00"):
            clean_number = clean_number[2:]

        if (
            not clean_number.isdigit()
            or len(clean_number) < 7
            or len(clean_number) > 15
        ):
            return None

        return "+" + clean_number

    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of Twilio SMS services.

        Returns:
            Dict with detailed health status
        """
        health_status = {
            "service": "twilio_sms",
            "timestamp": time.time(),
            "overall_status": ServiceStatus.HEALTHY.value,
            "services": {},
        }

        
        placeholder_numbers = ["+1234567890", "1234567890", "+15005550006"]
        if self.sms_from in placeholder_numbers:
            health_status["services"]["twilio_sms"] = {
                "status": ServiceStatus.UNHEALTHY.value,
                "configured": False,
                "from_number": self.sms_from,
                "message": f"Invalid from number: '{self.sms_from}' is a placeholder/test number. Please configure TWILIO_SMS_FROM_NUMBER with a verified number from your Twilio account.",
                "error": "Configuration error: placeholder phone number",
            }
            health_status["overall_status"] = ServiceStatus.UNHEALTHY.value
        elif self.is_sms_configured():
            try:
                if TWILIO_AVAILABLE and self.twilio_client:
                    account = self.twilio_client.api.accounts(self.account_sid).fetch()
                    health_status["services"]["twilio_sms"] = {
                        "status": ServiceStatus.HEALTHY.value,
                        "configured": True,
                        "account_status": account.status,
                        "from_number": self.sms_from,
                        "message": "Twilio SMS service is healthy",
                    }
                else:
                    health_status["services"]["twilio_sms"] = {
                        "status": ServiceStatus.DISABLED.value,
                        "configured": False,
                        "message": "Twilio SDK not available",
                    }
                    health_status["overall_status"] = ServiceStatus.DEGRADED.value
            except Exception as e:
                health_status["services"]["twilio_sms"] = {
                    "status": ServiceStatus.UNHEALTHY.value,
                    "configured": True,
                    "error": str(e),
                    "from_number": self.sms_from,
                    "message": "Twilio SMS service is unhealthy",
                }
                health_status["overall_status"] = ServiceStatus.UNHEALTHY.value
        else:
            missing_config = []
            if not self.twilio_client:
                missing_config.append("Twilio client")
            if not self.sms_from:
                missing_config.append("SMS from number")
                
            health_status["services"]["twilio_sms"] = {
                "status": ServiceStatus.DISABLED.value,
                "configured": False,
                "missing_config": missing_config,
                "message": f"Twilio SMS service not configured. Missing: {', '.join(missing_config)}",
            }
            health_status["overall_status"] = ServiceStatus.DISABLED.value

        if self.is_verify_configured():
            health_status["services"]["twilio_verify"] = {
                "status": (
                    ServiceStatus.HEALTHY.value
                    if self.twilio_client
                    else ServiceStatus.DISABLED.value
                ),
                "configured": True,
                "service_sid": self.verify_service_sid,
                "message": "Twilio Verify service is configured",
            }
        else:
            health_status["services"]["twilio_verify"] = {
                "status": ServiceStatus.DISABLED.value,
                "configured": False,
                "message": "Twilio Verify service not configured",
            }

        return health_status


twilio_sms_service = TwilioSMSService()


def validate_twilio_configuration():
    """
    Utility function to validate Twilio SMS configuration and provide helpful feedback.
    
    Returns:
        Dict with validation results and recommendations
    """
    validation = {
        "valid": False,
        "issues": [],
        "recommendations": [],
    }
    
    service = twilio_sms_service
    
    
    if not TWILIO_AVAILABLE:
        validation["issues"].append("Twilio SDK not installed")
        validation["recommendations"].append("Install Twilio SDK: pip install twilio")
        return validation
    
    
    if not service.account_sid:
        validation["issues"].append("TWILIO_ACCOUNT_SID not set")
        validation["recommendations"].append("Set TWILIO_ACCOUNT_SID environment variable")
    
    if not service.auth_token:
        validation["issues"].append("TWILIO_AUTH_TOKEN not set") 
        validation["recommendations"].append("Set TWILIO_AUTH_TOKEN environment variable")
    
    if not service.sms_from:
        validation["issues"].append("TWILIO_SMS_FROM_NUMBER not set")
        validation["recommendations"].append("Set TWILIO_SMS_FROM_NUMBER environment variable")
    elif service.sms_from in ["+1234567890", "1234567890", "+15005550006"]:
        validation["issues"].append(f"TWILIO_SMS_FROM_NUMBER is set to placeholder value: {service.sms_from}")
        validation["recommendations"].append(
            f"Replace {service.sms_from} with a verified phone number from your Twilio account. "
            "You can find verified numbers in the Twilio Console under Phone Numbers."
        )
    
    
    if service.account_sid and service.auth_token and service.twilio_client:
        try:
            account = service.twilio_client.api.accounts(service.account_sid).fetch()
            if account.status == 'active':
                validation["recommendations"].append("Twilio account is active and accessible")
            else:
                validation["issues"].append(f"Twilio account status: {account.status}")
        except Exception as e:
            validation["issues"].append(f"Cannot connect to Twilio API: {str(e)}")
            validation["recommendations"].append("Check your TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
    
    validation["valid"] = len(validation["issues"]) == 0
    
    return validation
