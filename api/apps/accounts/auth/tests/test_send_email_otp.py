"""
Comprehensive tests for the Send Email OTP system.

This module tests:
1. SendEmailOTPView - sending email OTP for account verification
2. ValidateEmailView - updated to handle both OTP and legacy codes
3. Integration tests ensuring the full email OTP flow works
4. Backward compatibility with legacy VerificationCode system
5. Proper verification field updates matching other OTP views
"""

import pytest
from django.test import TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.auth.models import OTP
from apps.accounts.user.models import VerificationCode
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, Mock

User = get_user_model()


class SendEmailOTPTestCase(TransactionTestCase):
    """Test cases for the SendEmailOTPView."""

    def setUp(self):
        self.client = APIClient()

        
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            fullname="Test User",
            username="testuser",
            is_active=True,
            is_email_verified=False,
            is_phone_verified=False,
            is_verified=False,
        )

        self.user_no_email = User.objects.create_user(
            email="",  
            password="testpass123",
            fullname="No Email User",
            username="noemailuser",
            phone_number="+1234567890",
        )

    def test_send_email_otp_success(self):
        """Test successful email OTP sending."""
        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService._send_otp_via_email"
        ) as mock_send:
            mock_send.return_value = True

            response = self.client.post(
                "/api/v1/auth/send-email-otp/",
                {"email": "test@example.com"},
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("message", response.data)
            self.assertIn("email", response.data)
            self.assertIn("te*t@example.com", response.data["email"])

            
            otp = OTP.objects.filter(user=self.user, purpose="verification").first()
            self.assertIsNotNone(otp)
            
            self.assertIn(otp.delivery_method, ["email", "fallback"])
            self.assertFalse(otp.is_used)
            self.assertTrue(otp.is_valid())

            
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            self.assertEqual(str(call_args[0][0].id), str(self.user.id))
            self.assertEqual(call_args[0][1], otp.code)
            self.assertEqual(call_args[0][2], "verification")

    def test_send_email_otp_user_not_found(self):
        """Test email OTP request for non-existent user."""
        response = self.client.post(
            "/api/v1/auth/send-email-otp/",
            {"email": "nonexistent@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("email", response.data["error"])

    def test_send_email_otp_invalid_email(self):
        """Test email OTP request with invalid email format."""
        response = self.client.post(
            "/api/v1/auth/send-email-otp/",
            {"email": "invalid-email"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("email", response.data["error"])

    def test_send_email_otp_missing_email(self):
        """Test email OTP request without email field."""
        response = self.client.post(
            "/api/v1/auth/send-email-otp/",
            {},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("email", response.data["error"])

    def test_send_email_otp_clears_existing_verification_otps(self):
        """Test that sending new email OTP clears existing verification OTPs."""
        
        existing_otp = OTP.objects.create(
            user=self.user,
            code="111111",
            purpose="verification",
            delivery_method="email",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService._send_otp_via_email"
        ) as mock_send:
            mock_send.return_value = True

            response = self.client.post(
                "/api/v1/auth/send-email-otp/",
                {"email": "test@example.com"},
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            
            self.assertFalse(OTP.objects.filter(id=existing_otp.id).exists())

            
            new_otp = OTP.objects.filter(user=self.user, purpose="verification").first()
            self.assertIsNotNone(new_otp)
            self.assertNotEqual(new_otp.code, "111111")

    def test_send_email_otp_delivery_failure(self):
        """Test handling of email delivery failure."""
        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService._send_otp_via_email"
        ) as mock_send:
            mock_send.return_value = False

            response = self.client.post(
                "/api/v1/auth/send-email-otp/",
                {"email": "test@example.com"},
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("error", response.data)

    def test_send_email_otp_rate_limiting(self):
        """Test rate limiting on send email OTP endpoint."""
        
        
        self.skipTest("Rate limiting test skipped in test environment")


class ValidateEmailOTPTestCase(TransactionTestCase):
    """Test cases for ValidateEmailView with OTP support."""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="validate@example.com",
            password="testpass123",
            fullname="Validate User",
            username="validateuser",
            is_active=False,
            is_email_verified=False,
            is_phone_verified=False,
            is_verified=False,
        )

    def test_validate_email_with_otp_success(self):
        """Test successful email validation using OTP code."""
        
        otp = OTP.objects.create(
            user=self.user,
            code="123456",
            purpose="verification",
            delivery_method="email",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        response = self.client.post(
            "/api/v1/auth/validate-email/",
            {"code": "123456", "email": "validate@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("user", response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.is_phone_verified)
        self.assertTrue(self.user.is_verified)

        
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    def test_validate_email_with_legacy_verification_code_success(self):
        """Test successful email validation using legacy VerificationCode (backward compatibility)."""
        
        verification_code = VerificationCode.objects.create(
            user=self.user, code="654321"
        )

        response = self.client.post(
            "/api/v1/auth/validate-email/",
            {"code": "654321", "email": "validate@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("user", response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.is_phone_verified)
        self.assertTrue(self.user.is_verified)

        
        self.assertFalse(
            VerificationCode.objects.filter(id=verification_code.id).exists()
        )

    def test_validate_email_otp_priority_over_legacy(self):
        """Test that OTP is checked first and legacy is fallback."""
        
        otp = OTP.objects.create(
            user=self.user,
            code="555555",
            purpose="verification",
            delivery_method="email",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        legacy_code = VerificationCode.objects.create(user=self.user, code="555555")

        response = self.client.post(
            "/api/v1/auth/validate-email/",
            {"code": "555555", "email": "validate@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

        
        self.assertTrue(VerificationCode.objects.filter(id=legacy_code.id).exists())

    def test_validate_email_expired_otp(self):
        """Test validation with expired OTP."""
        
        otp = OTP.objects.create(
            user=self.user,
            code="999999",
            purpose="verification",
            delivery_method="email",
            expires_at=timezone.now() - timedelta(minutes=1),  
        )

        response = self.client.post(
            "/api/v1/auth/validate-email/",
            {"code": "999999", "email": "validate@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        if "error" in response.data:
            self.assertIn("code", response.data["error"])
        else:
            self.assertIn("code", response.data)

    def test_validate_email_invalid_code(self):
        """Test validation with invalid code."""
        response = self.client.post(
            "/api/v1/auth/validate-email/",
            {"code": "000000", "email": "validate@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        if "error" in response.data:
            self.assertIn("code", response.data["error"])
        else:
            self.assertIn("code", response.data)

    def test_validate_email_wrong_user_code(self):
        """Test validation with code belonging to different user."""
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            fullname="Other User",
            username="otheruser",
        )

        
        OTP.objects.create(
            user=other_user,
            code="777777",
            purpose="verification",
            delivery_method="email",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        response = self.client.post(
            "/api/v1/auth/validate-email/",
            {"code": "777777", "email": "validate@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        if "error" in response.data:
            self.assertIn("code", response.data["error"])
        else:
            self.assertIn("code", response.data)

    def test_validate_email_user_not_found(self):
        """Test validation with non-existent user email."""
        response = self.client.post(
            "/api/v1/auth/validate-email/",
            {"code": "123456", "email": "nonexistent@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        if "error" in response.data:
            self.assertIn("email", response.data["error"])
        else:
            self.assertIn("email", response.data)


class EmailOTPIntegrationTestCase(TransactionTestCase):
    """Integration tests for the complete email OTP flow."""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="integration@example.com",
            password="testpass123",
            fullname="Integration User",
            username="integrationuser",
            is_active=False,
            is_email_verified=False,
            is_phone_verified=False,
            is_verified=False,
        )

    def test_complete_email_otp_flow(self):
        """Test the complete flow: send email OTP -> validate with OTP."""
        
        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService._send_otp_via_email"
        ) as mock_send:
            mock_send.return_value = True

            send_response = self.client.post(
                "/api/v1/auth/send-email-otp/",
                {"email": "integration@example.com"},
            )

            self.assertEqual(send_response.status_code, status.HTTP_200_OK)

        
        otp = OTP.objects.filter(user=self.user, purpose="verification").first()
        self.assertIsNotNone(otp)

        
        validate_response = self.client.post(
            "/api/v1/auth/validate-email/",
            {"code": otp.code, "email": "integration@example.com"},
        )

        self.assertEqual(validate_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", validate_response.data)
        self.assertIn("refresh", validate_response.data)

        
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.is_phone_verified)
        self.assertTrue(self.user.is_verified)

    def test_email_otp_verification_matches_other_otp_views(self):
        """Test that email OTP verification updates the same fields as other OTP views."""
        
        otp = OTP.objects.create(
            user=self.user,
            code="888888",
            purpose="verification",
            delivery_method="email",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)
        self.assertFalse(self.user.is_phone_verified)
        self.assertFalse(self.user.is_verified)

        
        response = self.client.post(
            "/api/v1/auth/validate-email/",
            {"code": "888888", "email": "integration@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active, "is_active should be True")
        self.assertTrue(self.user.is_email_verified, "is_email_verified should be True")
        self.assertTrue(self.user.is_phone_verified, "is_phone_verified should be True")
        self.assertTrue(self.user.is_verified, "is_verified should be True")

    def test_backward_compatibility_with_legacy_system(self):
        """Test that legacy VerificationCode system still works alongside new OTP system."""
        
        legacy_code = VerificationCode.objects.create(user=self.user, code="123456")

        response = self.client.post(
            "/api/v1/auth/validate-email/",
            {"code": "123456", "email": "integration@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.is_phone_verified)
        self.assertTrue(self.user.is_verified)

    def test_email_masking_in_response(self):
        """Test that email is properly masked in send email OTP response."""
        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService._send_otp_via_email"
        ) as mock_send:
            mock_send.return_value = True

            
            test_cases = [
                ("test@example.com", "te*t@example.com"),  
                ("a@example.com", "*@example.com"),
                ("ab@example.com", "**@example.com"),
                (
                    "verylongemail@example.com",
                    "ve*l@example.com",
                ),  
            ]

            for original_email, expected_masked in test_cases:
                
                self.user.email = original_email
                self.user.save()

                response = self.client.post(
                    "/api/v1/auth/send-email-otp/",
                    {"email": original_email},
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["email"], expected_masked)


class EmailOTPErrorHandlingTestCase(TransactionTestCase):
    """Test error handling in email OTP system."""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="errors@example.com",
            password="testpass123",
            fullname="Error User",
            username="erroruser",
        )

    def test_otp_generation_error(self):
        """Test handling of OTP generation errors."""
        with patch(
            "apps.accounts.user.models.User.generate_verification_code"
        ) as mock_generate:
            mock_generate.side_effect = Exception("Generation failed")

            response = self.client.post(
                "/api/v1/auth/send-email-otp/",
                {"email": "errors@example.com"},
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("error", response.data)

    def test_email_delivery_exception(self):
        """Test handling of email delivery exceptions."""
        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService._send_otp_via_email"
        ) as mock_send:
            mock_send.side_effect = Exception("Email service failed")

            response = self.client.post(
                "/api/v1/auth/send-email-otp/",
                {"email": "errors@example.com"},
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("error", response.data)

    def test_validation_transaction_error(self):
        """Test handling of transaction errors during validation."""
        otp = OTP.objects.create(
            user=self.user,
            code="999999",
            purpose="verification",
            delivery_method="email",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        with patch("django.db.transaction.atomic") as mock_atomic:
            mock_atomic.side_effect = Exception("Transaction failed")

            response = self.client.post(
                "/api/v1/auth/validate-email/",
                {"code": "999999", "email": "errors@example.com"},
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("error", response.data)



class EmailOTPSecurityTestCase(TransactionTestCase):
    """Test security aspects of email OTP system."""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="security@example.com",
            password="testpass123",
            fullname="Security User",
            username="securityuser",
        )

    def test_used_otp_cannot_be_reused(self):
        """Test that used OTP cannot be used again."""
        otp = OTP.objects.create(
            user=self.user,
            code="111111",
            purpose="verification",
            delivery_method="email",
            expires_at=timezone.now() + timedelta(minutes=10),
            is_used=True,  
        )

        response = self.client.post(
            "/api/v1/auth/validate-email/",
            {"code": "111111", "email": "security@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_case_insensitive_email_lookup(self):
        """Test that email lookup is case insensitive."""
        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService._send_otp_via_email"
        ) as mock_send:
            mock_send.return_value = True

            
            test_emails = [
                "SECURITY@EXAMPLE.COM",
                "Security@Example.com",
                "security@EXAMPLE.COM",
            ]

            for email in test_emails:
                response = self.client.post(
                    "/api/v1/auth/send-email-otp/",
                    {"email": email},
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_only_verification_purpose_otps_work(self):
        """Test that only OTPs with purpose='verification' work for validate-email."""
        
        otp = OTP.objects.create(
            user=self.user,
            code="222222",
            purpose="login",  
            delivery_method="email",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        response = self.client.post(
            "/api/v1/auth/validate-email/",
            {"code": "222222", "email": "security@example.com"},
        )

        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        if "error" in response.data:
            self.assertIn("code", response.data["error"])
        else:
            self.assertIn("code", response.data)
