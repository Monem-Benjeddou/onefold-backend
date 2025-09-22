"""
Simple SMS routing service for country-based service selection.
Routes SMS to Neons for Saudi Arabia (+966) and Twilio for all other countries.
"""

import re
import logging
from typing import Dict, Any, Optional
from enum import Enum

from .twilio_sms_service import twilio_sms_service, CommunicationResult
from apps.notifications.services.neons_sms_service import NeonsSMSService

logger = logging.getLogger(__name__)


class SMSProvider(Enum):
    NEONS = "neons"
    TWILIO = "twilio"


class SMSRouter:
    """
    Simple SMS routing service that selects the appropriate SMS provider
    based on phone number country code.

    Routing Strategy:
    - Saudi Arabia (+966): Neons SMS Service
    - All other countries: Twilio SMS Service
    - No retries, no fallbacks - single attempt only
    """

    def __init__(self):
        self._initialize_services()


    def _initialize_services(self):
        """Initialize SMS services."""
        self.neons_service = NeonsSMSService()
        self.services = {
            SMSProvider.NEONS: self.neons_service,
            SMSProvider.TWILIO: twilio_sms_service,
        }

    def _detect_provider(self, phone_number: str) -> SMSProvider:
        """
        Detect the appropriate SMS provider for a phone number.
        
        Args:
            phone_number: Phone number to analyze
            
        Returns:
            SMSProvider: NEONS for Saudi (+966), TWILIO for all others
        """
        clean_number = self._normalize_phone_number(phone_number)
        
        
        if clean_number.startswith("966"):
            return SMSProvider.NEONS
            
        
        return SMSProvider.TWILIO

    def _normalize_phone_number(self, phone_number: str) -> str:
        """Normalize phone number for country code detection."""
        if not phone_number:
            return ""

        clean = re.sub(r"[^\d]", "", phone_number)

        if clean.startswith("00"):
            clean = clean[2:]
        elif phone_number.startswith("+"):
            pass

        return clean

    def send_sms(
        self,
        phone_number: str,
        message: str,
        force_provider: Optional[SMSProvider] = None,
        **kwargs,
    ) -> CommunicationResult:
        """
        Send SMS using simple routing - single attempt, no retries.

        Args:
            phone_number: Recipient phone number
            message: SMS message content
            force_provider: Override routing and use specific provider
            **kwargs: Additional parameters passed to the SMS service

        Returns:
            CommunicationResult with delivery status
        """
        if not phone_number or not message:
            return CommunicationResult(
                success=False,
                error="Phone number and message are required",
                service_used="router",
            )

        
        if force_provider:
            provider = force_provider
        else:
            provider = self._detect_provider(phone_number)

        
        return self._send_via_provider(provider, phone_number, message, **kwargs)

    def _send_via_provider(
        self, provider: SMSProvider, phone_number: str, message: str, **kwargs
    ) -> CommunicationResult:
        """Send SMS via specific provider - single attempt only."""
        service = self.services.get(provider)

        if not service:
            return CommunicationResult(
                success=False,
                error=f"SMS provider {provider.value} not available",
                service_used=provider.value,
            )

        try:
            if provider == SMSProvider.NEONS:
                neons_result = service.send_sms(phone_number, message)
                return CommunicationResult(
                    success=neons_result.get("success", False),
                    message_id=(
                        neons_result.get("response", {}).get("id")
                        if isinstance(neons_result.get("response"), dict)
                        else None
                    ),
                    error=neons_result.get("error"),
                    service_used="neons_sms",
                )
            elif provider == SMSProvider.TWILIO:
                return service.send_sms(phone_number, message, **kwargs)
            else:
                return CommunicationResult(
                    success=False,
                    error=f"Unknown SMS provider: {provider.value}",
                    service_used=provider.value,
                )
        except Exception as e:
            logger.error(f"SMS sending failed via {provider.value}: {str(e)}")
            return CommunicationResult(
                success=False, error=str(e), service_used=provider.value
            )

    def send_otp_sms(
        self, phone_number: str, otp_code: str, otp_type: str = "login", **kwargs
    ) -> CommunicationResult:
        """
        Send OTP SMS using simple routing with standardized templates.

        Args:
            phone_number: Target phone number
            otp_code: OTP code to send
            otp_type: Type of OTP (login, registration, password_reset)

        Returns:
            CommunicationResult with delivery status
        """
        otp_templates = {
            "login": "Your Kolct login OTP code is: {}. Valid for 10 minutes.",
            "registration": "Welcome to Kolct! Your registration OTP code is: {}. Valid for 10 minutes.",
            "password_reset": "Your Kolct password reset OTP code is: {}. Valid for 10 minutes.",
            "verification": "Your Kolct verification OTP code is: {}. Valid for 10 minutes.",
        }

        template = otp_templates.get(otp_type, otp_templates["login"])
        message = template.format(otp_code)

        return self.send_sms(phone_number, message, **kwargs)


    def get_routing_status(self) -> Dict[str, Any]:
        """
        Get simple routing status and service health.

        Returns:
            Dict with routing configuration and service status
        """
        status = {
            "routing_rules": {
                "saudi_arabia": {
                    "country_codes": ["966"],
                    "service": "neons"
                },
                "international": {
                    "country_codes": ["all_others"],
                    "service": "twilio"
                }
            },
            "services": {}
        }

        for provider, service in self.services.items():
            try:
                if hasattr(service, "health_check"):
                    health = service.health_check()
                    status["services"][provider.value] = health
                else:
                    if hasattr(service, "is_configured"):
                        is_configured = service.is_configured()
                    elif hasattr(service, "is_sms_configured"):
                        is_configured = service.is_sms_configured()
                    else:
                        is_configured = False

                    status["services"][provider.value] = {
                        "status": "healthy" if is_configured else "disabled",
                        "configured": is_configured,
                    }
            except Exception as e:
                status["services"][provider.value] = {
                    "status": "unhealthy",
                    "error": str(e),
                }

        return status



sms_router = SMSRouter()
