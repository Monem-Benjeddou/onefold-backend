"""
Management command to test SMS service functionality.

This command allows testing the Neons SMS integration and fallback services
without requiring a full OTP flow.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.notifications.services import neons_sms_service

from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService
import json

User = get_user_model()


class Command(BaseCommand):
    help = "Test SMS service functionality"

    def add_arguments(self, parser):
        parser.add_argument(
            "--phone",
            type=str,
            help="Phone number to send test SMS to (e.g. +21626716816)",
        )
        parser.add_argument(
            "--message",
            type=str,
            default="Test message from Kolct API",
            help='Custom message to send (default: "Test message from Kolct API")',
        )
        parser.add_argument(
            "--test-otp",
            action="store_true",
            help="Test OTP delivery using a test user",
        )
        parser.add_argument(
            "--user-email",
            type=str,
            help="Email of existing user to test OTP delivery (requires --test-otp)",
        )
        parser.add_argument(
            "--health-check",
            action="store_true",
            help="Perform SMS service health check only",
        )
        parser.add_argument(
            "--config-check",
            action="store_true",
            help="Check SMS service configuration and environment variables",
        )
        parser.add_argument(
            "--endpoint-test",
            action="store_true",
            help="Test connectivity to Neons API endpoints",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== SMS Service Test ===\n"))

        if options["config_check"]:
            self.check_configuration()
            return

        if options["endpoint_test"]:
            self.test_endpoints()
            return

        if options["health_check"]:
            self.perform_health_check()
            return

        if options["test_otp"]:
            self.test_otp_delivery(options.get("user_email"))
            return

        phone_number = options.get("phone")
        if not phone_number:
            raise CommandError("Please provide a phone number with --phone argument")

        message = options.get("message", "Test message from Kolct API")
        self.test_direct_sms(phone_number, message)

    def perform_health_check(self):
        """Perform health check of SMS services."""
        self.stdout.write("Performing SMS service health check...\n")

        health = neons_sms_service.health_check()
        self.stdout.write(f"Neons SMS Service Status:")
        self.stdout.write(json.dumps(health, indent=2))

        if health["status"] == "healthy":
            self.stdout.write(self.style.SUCCESS("✓ Neons SMS service is healthy"))
        elif health["status"] == "warning":
            self.stdout.write(
                self.style.WARNING("⚠ Neons SMS service has staging limitations")
            )
            if "note" in health:
                self.stdout.write(f"  Note: {health['note']}")
        else:
            self.stdout.write(self.style.ERROR("✗ Neons SMS service has issues"))

        self.stdout.write("")

    def test_direct_sms(self, phone_number: str, message: str):
        """Test direct SMS sending."""
        self.stdout.write(f"Testing direct SMS to: {phone_number}")
        self.stdout.write(f"Message: {message}\n")

        self.stdout.write("Testing Neons SMS service directly...")
        if neons_sms_service.is_configured():
            result = neons_sms_service.send_sms(phone_number, message)
            if result["success"]:
                self.stdout.write(self.style.SUCCESS("✓ Neons SMS sent successfully"))
                self.stdout.write(f"  Phone: {result.get('phone_number')}")
            else:
                self.stdout.write(self.style.ERROR("✗ Neons SMS failed"))
                self.stdout.write(f"  Error: {result.get('error', 'Unknown error')}")
        else:
            self.stdout.write(self.style.WARNING("⚠ Neons SMS service not configured"))

        self.stdout.write("")

        self.stdout.write("Testing integrated SMS with fallback...")
        result = neons_sms_service.send_sms(phone_number, message)
        success = result.get("success", False)
        if success:
            self.stdout.write(
                self.style.SUCCESS("✓ SMS sent successfully (via some service)")
            )
        else:
            self.stdout.write(self.style.ERROR("✗ All SMS services failed"))

        self.stdout.write("")

    def test_otp_delivery(self, user_email: str = None):
        """Test OTP delivery system."""
        self.stdout.write("Testing OTP delivery system...\n")

        if user_email:
            user = User.objects.filter(email=user_email).first()
            if not user:
                raise CommandError(f"User with email {user_email} not found")
        else:

            user = (
                User.objects.filter(phone_number__isnull=False)
                .exclude(phone_number="")
                .first()
            )
            if not user:
                raise CommandError(
                    "No users with phone numbers found. Please create a test user first."
                )

        self.stdout.write(f"Using test user: {user.email}")
        self.stdout.write(f"Phone number: {user.phone_number}")

        is_valid, error_message = OTPDeliveryService.validate_user_for_otp_delivery(
            user
        )
        if not is_valid:
            self.stdout.write(
                self.style.ERROR(f"User validation failed: {error_message}")
            )
            return

        test_otp = "123456"
        self.stdout.write(f"Sending test OTP: {test_otp}")

        success = OTPDeliveryService.send_otp(user, test_otp, "testing")

        if success:
            delivery_target = OTPDeliveryService.get_delivery_target_display(user)
            self.stdout.write(
                self.style.SUCCESS(f"✓ OTP sent successfully to {delivery_target}")
            )
        else:
            self.stdout.write(self.style.ERROR("✗ OTP delivery failed"))

        self.stdout.write("")

    def check_configuration(self):
        """Check SMS service configuration."""
        from django.conf import settings

        self.stdout.write(self.style.SUCCESS("=== SMS Configuration Check ===\n"))

        config_items = [
            ("NEONS_SMS_BASE_URL", getattr(settings, "NEONS_SMS_BASE_URL", "NOT SET")),
            (
                "NEONS_SMS_CLIENT_ID",
                getattr(settings, "NEONS_SMS_CLIENT_ID", "NOT SET"),
            ),
            (
                "NEONS_SMS_CLIENT_SECRET",
                (
                    "***HIDDEN***"
                    if getattr(settings, "NEONS_SMS_CLIENT_SECRET", "")
                    else "NOT SET"
                ),
            ),
            (
                "OTP_DELIVERY_METHOD",
                getattr(settings, "OTP_DELIVERY_METHOD", "NOT SET"),
            ),
        ]

        self.stdout.write("Environment Variables:")
        for key, value in config_items:
            status = "✓" if value and value != "NOT SET" else "✗"
            color = self.style.SUCCESS if status == "✓" else self.style.ERROR
            self.stdout.write(f"  {color(status)} {key}: {value}")

        self.stdout.write("")

        is_configured = neons_sms_service.is_configured()
        if is_configured:
            self.stdout.write(
                self.style.SUCCESS("✓ Neons SMS service is properly configured")
            )
        else:
            self.stdout.write(
                self.style.ERROR("✗ Neons SMS service is not properly configured")
            )

        delivery_method = OTPDeliveryService.get_delivery_method()
        self.stdout.write(f"Current OTP delivery method: {delivery_method}")

        self.stdout.write("")

    def test_endpoints(self):
        """Test connectivity to various Neons API endpoints."""
        import requests
        from django.conf import settings

        self.stdout.write(self.style.SUCCESS("=== Neons API Endpoint Test ===\n"))

        base_urls = [
            getattr(settings, "NEONS_SMS_BASE_URL", ""),
            "https://neons-stg-gateway.neons.sa",
            "https://gateway.neons.sa",
            "https://api.neons.sa",
            "https://sms.neons.sa",
            "https://integrationgateway.neons.sa",
        ]

        keycloak_endpoints = [
            "https://neons-stg-keycloak.neons.sa/realms/neons/protocol/openid-connect/token"
        ]

        endpoints = [
            "/identity/client-credentials",
            "/auth/token",
            "/oauth/token",
            "/api/auth/token",
            "/api/identity/client-credentials",
            "/token",
            "/swagger",
            "/health",
            "/api/health",
        ]

        for base_url in base_urls:
            if not base_url:
                continue

            self.stdout.write(f"Testing base URL: {base_url}")

            try:
                response = requests.get(base_url, timeout=10)
                status_color = (
                    self.style.SUCCESS
                    if response.status_code < 400
                    else self.style.WARNING
                )
                self.stdout.write(f"  Root: {status_color(response.status_code)}")
            except Exception as e:
                self.stdout.write(
                    f'  Root: {self.style.ERROR("Connection failed")} - {str(e)}'
                )

            for endpoint in endpoints:
                url = f"{base_url}{endpoint}"
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        status_color = self.style.SUCCESS
                    elif response.status_code == 404:
                        status_color = self.style.WARNING
                    else:
                        status_color = self.style.ERROR
                    self.stdout.write(
                        f"  {endpoint}: {status_color(response.status_code)}"
                    )
                except Exception:
                    continue

            self.stdout.write("")

        self.stdout.write(f"Testing Keycloak authentication endpoints:")
        for keycloak_url in keycloak_endpoints:
            try:
                response = requests.get(keycloak_url, timeout=10)
                if response.status_code == 200:
                    status_color = self.style.SUCCESS
                    self.stdout.write(
                        f"  {keycloak_url}: {status_color(response.status_code)} ✓"
                    )
                elif response.status_code == 405:
                    status_color = self.style.SUCCESS
                    self.stdout.write(
                        f'  {keycloak_url}: {status_color("405 - Method Not Allowed (Expected)")} ✓'
                    )
                else:
                    status_color = self.style.WARNING
                    self.stdout.write(
                        f"  {keycloak_url}: {status_color(response.status_code)}"
                    )
            except Exception as e:
                self.stdout.write(
                    f'  {keycloak_url}: {self.style.ERROR("Connection failed")} - {str(e)}'
                )

        self.stdout.write("")

    def style_header(self, text):
        """Style a header with borders."""
        border = "=" * len(text)
        return f"\n{border}\n{text}\n{border}\n"
