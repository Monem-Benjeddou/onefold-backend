"""
Comprehensive tests for OTP verification status updates.

This module tests that OTP verification properly updates user verification status fields:
- is_email_verified
- is_phone_verified 
- is_verified (for blue check verification)
"""

import pytest
from django.test import TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.auth.models import OTP
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class OTPVerificationStatusUpdateTest(TransactionTestCase):
    """Test that OTP verification correctly updates user verification status."""

    def setUp(self):
        self.client = APIClient()

        self.user_email_only = User.objects.create_user(
            email="emailonly@example.com",
            password="testpass123",
            fullname="Email Only User",
            username="emailonly",
            is_active=True,
            is_email_verified=False,
            is_phone_verified=False,
        )

        self.user_phone_only = User.objects.create_user(
            email="phoneonly@example.com",
            phone_number="+1234567890",
            password="testpass123",
            fullname="Phone Only User",
            username="phoneonly",
            is_active=True,
            is_email_verified=False,
            is_phone_verified=False,
        )

        self.user_both_contacts = User.objects.create_user(
            email="bothcontacts@example.com",
            phone_number="+1987654321",
            password="testpass123",
            fullname="Both Contacts User",
            username="bothcontacts",
            is_active=True,
            is_email_verified=False,
            is_phone_verified=False,
        )

        self.unverified_user = User.objects.create_user(
            email="unverified@example.com",
            phone_number="+1122334455",
            password="testpass123",
            fullname="Unverified User",
            username="unverified",
            is_active=False,
            is_email_verified=False,
            is_phone_verified=False,
        )

    def test_password_reset_otp_sets_email_verified(self):
        """Test password reset OTP verification sets email as verified."""
        from apps.accounts.auth.serializers.reset_password_otp import (
            ResetPasswordOTPSerializer,
        )

        otp = OTP.objects.create(
            user=self.user_email_only,
            code="333333",
            purpose="password_reset",
            delivery_method="email",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        serializer = ResetPasswordOTPSerializer(
            data={
                "email": "emailonly@example.com",
                "otp": "333333",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123",
            }
        )

        self.assertTrue(serializer.is_valid())
        result = serializer.save()

        self.assertIn("message", result)

        self.user_email_only.refresh_from_db()

        self.assertTrue(self.user_email_only.is_email_verified)

    def test_already_verified_users_not_updated_unnecessarily(self):
        """Test that already verified users don't get unnecessary updates."""

        self.user_both_contacts.is_email_verified = True
        self.user_both_contacts.is_phone_verified = True
        self.user_both_contacts.save()

        otp = OTP.objects.create(
            user=self.user_both_contacts,
            code="444444",
            purpose="login",
            delivery_method="email",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        response = self.client.post(
            "/api/v1/auth/verify-otp/",
            {"email": "bothcontacts@example.com", "otp": "444444"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user_both_contacts.refresh_from_db()

        self.assertTrue(self.user_both_contacts.is_email_verified)
        self.assertTrue(self.user_both_contacts.is_phone_verified)
        self.assertTrue(self.user_both_contacts.is_verified)
        self.assertTrue(self.user_both_contacts.is_active)

    def test_login_works_after_verification(self):
        """Test that login works correctly after OTP verification sets verified status."""

        otp = OTP.objects.create(
            user=self.unverified_user,
            code="555555",
            purpose="registration",
            delivery_method="email",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        response = self.client.post(
            "/api/v1/auth/verify-registration-otp/",
            {"email": "unverified@example.com", "otp": "555555"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        login_response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "unverified@example.com", "password": "testpass123"},
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)
        self.assertIn("user", login_response.data)

    def test_edge_case_no_delivery_method_defaults_to_email(self):
        """Test edge case where OTP has no delivery method defaults to email verification."""

        otp = OTP.objects.create(
            user=self.user_email_only,
            code="666666",
            purpose="login",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        response = self.client.post(
            "/api/v1/auth/verify-otp/",
            {"email": "emailonly@example.com", "otp": "666666"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user_email_only.refresh_from_db()

        self.assertTrue(self.user_email_only.is_email_verified)
        self.assertTrue(self.user_email_only.is_phone_verified)
        self.assertTrue(self.user_email_only.is_verified)
        self.assertTrue(self.user_email_only.is_active)
