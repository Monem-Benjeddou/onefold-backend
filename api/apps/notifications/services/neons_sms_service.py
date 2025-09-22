"""
Neons SMS Service

SMS service implementation for the Neons SMS API integration.
Handles OAuth2 client credentials authentication and SMS delivery through the Neons gateway.
"""

import logging
import requests
from django.conf import settings
from django.core.cache import cache
from datetime import datetime
from typing import Optional, Dict, Any
import re

logger = logging.getLogger(__name__)


class NeonsSMSException(Exception):
    """Custom exception for Neons SMS API errors."""

    pass


class NeonsSMSService:
    """
    Service for sending SMS messages via the Neons SMS API.

    Features:
    - OAuth2 client credentials authentication with token caching
    - Retry logic for failed requests
    - Phone number validation and formatting
    - Comprehensive error handling and logging
    """

    CACHE_KEY_ACCESS_TOKEN = "neons_sms_access_token"

    def __init__(self):
        """Initialize the Neons SMS service with configuration."""
        self.base_url = getattr(settings, "NEONS_SMS_BASE_URL", "").rstrip("/")
        self.client_id = getattr(settings, "NEONS_SMS_CLIENT_ID", "")
        self.client_secret = getattr(settings, "NEONS_SMS_CLIENT_SECRET", "")
        self.auth_url = getattr(settings, "NEONS_SMS_AUTH_URL", "")
        self.token_cache_ttl = getattr(settings, "NEONS_SMS_TOKEN_CACHE_TTL", 3600)

        if not all([self.base_url, self.client_id, self.client_secret]):
            logger.warning(
                "Neons SMS service not properly configured. "
                "Missing NEONS_SMS_BASE_URL, NEONS_SMS_CLIENT_ID, or NEONS_SMS_CLIENT_SECRET"
            )

    def is_configured(self) -> bool:
        """
        Check if the SMS service is properly configured.

        Returns:
            bool: True if all required settings are present
        """
        return bool(self.base_url and self.client_id and self.client_secret)

    def _get_cached_token(self) -> Optional[str]:
        """Retrieve cached access token if available and not expired."""
        return cache.get(self.CACHE_KEY_ACCESS_TOKEN)

    def _cache_token(self, token: str) -> None:
        """Cache the access token with appropriate TTL."""

        cache_ttl = max(self.token_cache_ttl - 60, 300)
        cache.set(self.CACHE_KEY_ACCESS_TOKEN, token, timeout=cache_ttl)
        logger.info("SMS access token cached successfully")

    def _authenticate(self) -> str:
        """
        Authenticate with Neons Integration Gateway API using OAuth2 client credentials flow.
        Uses the integration gateway OAuth2 token endpoint.

        Returns:
            str: Access token for API requests

        Raises:
            NeonsSMSException: If authentication fails
        """

        if self.auth_url:
            auth_url = self.auth_url
        else:
            auth_url = f"{self.base_url}/oauth2/token"

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            logger.info(f"Attempting Integration Gateway authentication at: {auth_url}")
            response = requests.post(
                auth_url, data=payload, headers=headers, timeout=30
            )

            logger.info(
                f"Integration Gateway authentication response: HTTP {response.status_code}"
            )

            if response.status_code == 200:
                try:
                    token_data = response.json()
                    access_token = token_data.get("access_token")

                    if access_token:

                        expires_in = token_data.get("expires_in", 300)
                        self.token_cache_ttl = min(expires_in, self.token_cache_ttl)

                        self._cache_token(access_token)
                        logger.info(
                            f"Successfully authenticated with Integration Gateway - expires in {expires_in}s"
                        )
                        return access_token
                    else:
                        error_msg = f"No access_token received from Integration Gateway: {token_data}"
                        logger.error(error_msg)
                        raise NeonsSMSException(error_msg)

                except ValueError as e:
                    error_msg = f"Invalid JSON response from Integration Gateway: {e} - Response: {response.text}"
                    logger.error(error_msg)
                    raise NeonsSMSException(error_msg)

            elif response.status_code in [400, 401, 403]:

                error_msg = f"Integration Gateway authentication failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise NeonsSMSException(error_msg)

            else:

                error_msg = f"Integration Gateway server error: HTTP {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise NeonsSMSException(error_msg)

        except requests.RequestException as e:
            error_msg = f"Network error connecting to Integration Gateway: {str(e)}"
            logger.error(error_msg)
            raise NeonsSMSException(error_msg)

    def get_access_token(self) -> str:
        """
        Get a valid access token, using cache when possible.

        Returns:
            str: Valid access token

        Raises:
            NeonsSMSException: If unable to obtain token
        """

        cached_token = self._get_cached_token()
        if cached_token:
            logger.debug("Using cached SMS access token")
            return cached_token

        return self._authenticate()

    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number to ensure it's in the correct format.

        Args:
            phone_number (str): Raw phone number

        Returns:
            str: Formatted phone number with country code
        """

        clean_number = "".join(filter(str.isdigit, phone_number))

        if clean_number.startswith("00"):

            return "+" + clean_number[2:]

        if clean_number.startswith("216"):
            return "+" + clean_number

        if not clean_number.startswith("966"):
            if clean_number.startswith("0"):
                clean_number = "966" + clean_number[1:]
            else:
                clean_number = "966" + clean_number

        return "+" + clean_number

    def validate_and_format_phone_number(self, phone_number: str) -> Optional[str]:
        """
        Validate and format phone number, returning None if invalid.

        Args:
            phone_number (str): Raw phone number

        Returns:
            Optional[str]: Formatted phone number if valid, None if invalid
        """
        try:

            if not phone_number or not any(char.isdigit() for char in phone_number):
                return None

            clean_number = "".join(filter(str.isdigit, phone_number))

            if len(clean_number) < 8 or len(clean_number) > 15:
                return None

            if phone_number.startswith("+"):

                if len(clean_number) < 10:
                    return None
                return phone_number

            return self._format_phone_number(phone_number)
        except Exception:
            return None

    def send_sms(
        self, phone_number: str, message: str
    ) -> Dict[str, Any]:
        """
        Send SMS message via Neons API - single attempt only.

        Args:
            phone_number (str): Recipient phone number
            message (str): SMS message content

        Returns:
            Dict[str, Any]: Response containing success status and details
        """
        if not self.is_configured():
            logger.error("Cannot send SMS: Neons SMS service is not configured")
            return {
                "success": False,
                "error": "SMS service not configured",
                "phone_number": phone_number,
                "message": message,
            }

        formatted_phone = self.validate_and_format_phone_number(phone_number)
        if not formatted_phone:
            logger.error(f"Invalid phone number: {phone_number}")
            return {
                "success": False,
                "error": "Invalid phone number",
                "phone_number": phone_number,
                "message": message,
            }

        if not message or not message.strip():
            logger.error("Cannot send empty SMS message")
            return {
                "success": False,
                "error": "Empty message not allowed",
                "phone_number": formatted_phone,
                "message": message,
            }

        try:
            access_token = self.get_access_token()
            return self._send_oauth_sms(formatted_phone, message, access_token)
        except NeonsSMSException as e:
            logger.error(f"SMS sending error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "phone_number": formatted_phone,
                "message": message,
            }

    def _send_oauth_sms(
        self, phone_number: str, message: str, access_token: str
    ) -> Dict[str, Any]:
        """
        Send SMS using OAuth2 Bearer token authentication.

        Args:
            phone_number: Formatted phone number
            message: SMS message content
            access_token: OAuth2 access token

        Returns:
            Dict[str, Any]: Response containing success status and details
        """

        sms_url = f"{self.base_url}/SMS"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        payload = {"PhoneNumber": phone_number, "Template": message}

        try:
            logger.info(f"Sending SMS to {phone_number} via {sms_url}")
            response = requests.post(sms_url, json=payload, headers=headers, timeout=30)

            logger.info(f"SMS response: HTTP {response.status_code}")

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    is_sent = response_data.get("isSent", False)

                    if is_sent:
                        logger.info(f"SMS sent successfully to {phone_number}")
                        return {
                            "success": True,
                            "phone_number": phone_number,
                            "message": message,
                            "response": response_data,
                        }
                    else:
                        logger.warning(
                            f"SMS not sent according to API response: {response_data}"
                        )
                        return {
                            "success": False,
                            "error": "SMS not sent according to API response",
                            "phone_number": phone_number,
                            "message": message,
                            "response": response_data,
                        }
                except ValueError:

                    logger.info(
                        f"SMS sent successfully to {phone_number} (non-JSON response)"
                    )
                    return {
                        "success": True,
                        "phone_number": phone_number,
                        "message": message,
                        "response": response.text,
                    }

            elif response.status_code == 401:
                logger.warning("OAuth token expired or invalid")
                return {
                    "success": False,
                    "error": "Authentication failed",
                    "status_code": 401,
                    "phone_number": phone_number,
                    "message": message,
                }

            else:
                error_msg = (
                    f"SMS API returned status {response.status_code}: {response.text}"
                )
                logger.error(error_msg)

                if response.status_code == 404:
                    logger.error(
                        f"SMS API 404 Error - Check endpoint URL: {self.base_url}/SMS"
                    )
                    logger.error(
                        f"Full request details - Headers: {{'Authorization': 'Bearer [REDACTED]', 'Content-Type': 'application/json'}}"
                    )
                    logger.error(
                        f"Payload: {{'PhoneNumber': '{phone_number}', 'Template': '[MESSAGE_REDACTED]'}}"
                    )

                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code,
                    "phone_number": phone_number,
                    "message": message,
                }

        except requests.RequestException as e:
            error_msg = f"Network error sending SMS: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "phone_number": phone_number,
                "message": message,
            }

    def send_otp_sms(
        self, phone_number: str, otp_code: str, otp_type: str = "login"
    ) -> Dict[str, Any]:
        """
        Send OTP SMS with predefined templates.

        Args:
            phone_number: Target phone number
            otp_code: 6-digit OTP code
            otp_type: Type of OTP (login, password_reset, verification)

        Returns:
            Dict[str, Any]: Response containing success status and details
        """

        templates = {
            "login": "Your Kolct login OTP code is: {}. Valid for 10 minutes.",
            "password_reset": "Your Kolct password reset OTP code is: {}. Valid for 10 minutes.",
            "verification": "Your Kolct verification OTP code is: {}. Valid for 10 minutes.",
            "registration": "Welcome to Kolct! Your registration OTP code is: {}. Valid for 10 minutes.",
        }

        template = templates.get(otp_type, templates["login"])
        message = template.format(otp_code)

        logger.info(f"Sending {otp_type} OTP SMS to {phone_number}")
        result = self.send_sms(phone_number, message)
        result["otp_type"] = otp_type
        return result

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the SMS service.

        Returns:
            Dict with health check results
        """
        health = {
            "service": "Neons SMS",
            "configured": self.is_configured(),
            "timestamp": datetime.now().isoformat(),
        }

        if not self.is_configured():
            health["status"] = "error"
            health["message"] = "Service not configured"
            return health

        try:
            token = self.get_access_token()
            health["status"] = "healthy"
            health["message"] = "Authentication successful"
            health["base_url"] = self.base_url
            health["authentication"] = "ok"
        except NeonsSMSException as e:
            error_msg = str(e)
            if "Network error connecting to Integration Gateway" in error_msg:
                health["status"] = "warning"
                health["message"] = (
                    "Cannot connect to Integration Gateway authentication service. "
                    "This may be a network issue or service unavailability."
                )
                health["base_url"] = self.base_url
                health["auth_url"] = f"{self.base_url}/oauth2/token"
                health["authentication"] = "network_error"
                health["note"] = (
                    "Service will work when Integration Gateway is accessible"
                )
            elif "Integration Gateway authentication failed" in error_msg:
                health["status"] = "unhealthy"
                health["message"] = (
                    "Integration Gateway authentication failed - check client credentials"
                )
                health["base_url"] = self.base_url
                health["auth_url"] = f"{self.base_url}/oauth2/token"
                health["authentication"] = "credentials_error"
            else:
                health["status"] = "unhealthy"
                health["message"] = f"Authentication failed: {error_msg}"
                health["base_url"] = self.base_url
                health["authentication"] = "failed"
        except Exception as e:
            health["status"] = "error"
            health["message"] = f"Health check error: {str(e)}"
            health["base_url"] = self.base_url
            health["authentication"] = "error"

        return health

    def send_sms_simple(self, phone_number: str, message: str) -> bool:
        """
        Simple SMS send method that returns only boolean for backward compatibility.

        Args:
            phone_number (str): Recipient phone number
            message (str): SMS message content

        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        result = self.send_sms(phone_number, message)
        return result.get("success", False)


neons_sms_service = NeonsSMSService()
