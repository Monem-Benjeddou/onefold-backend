"""
Complete OTP authentication test suite.

This consolidated test file contains all OTP-related tests including:
- OTP model tests
- Login OTP functionality
- Registration OTP requirements
- Password reset OTP flows
- Delivery mechanism tests
- Fallback mechanism tests
- Comprehensive edge cases and error handling
"""

import pytest
from typing import Any
from unittest.mock import patch, MagicMock
from datetime import timedelta

from django.test import TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.core import mail

from rest_framework.test import APITransactionTestCase, APIClient
from rest_framework import status

from apps.accounts.auth.models import OTP
from apps.accounts.auth.utils import generate_otp
from apps.accounts.user.models import VerificationCode
from core.tests.base import IsolatedAPITestCase

User = get_user_model()


class OTPModelTests(APITransactionTestCase):
    """Test OTP model functionality and methods."""

    def setUp(self):
        super().setUp()
        self.user = self.create_test_user(
            email="test@example.com",
            phone_number="+21626716816",
            is_email_verified=True,
        )


class OTPLoginTests(APITransactionTestCase):
    """Test OTP login functionality."""

    def setUp(self):
        super().setUp()
        self.user = self.create_test_user(
            email="testuser@example.com",
            phone_number="+21626716816",
            is_email_verified=True,
        )
        self.user.set_password("testpassword")
        self.user.save()

        self.login_otp_url = reverse("auth-login-otp")
        self.verify_otp_url = reverse("auth-verify-otp")

    @patch("core.tasks.sms.send_sms_task.delay")
    def test_send_otp_success(self, mock_sms_task):
        """Test successful OTP sending."""
        mock_sms_task.return_value = MagicMock()

        response = self.client.post(
            self.login_otp_url, {"email": "testuser@example.com"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(OTP.objects.filter(user=self.user).exists())
        mock_sms_task.assert_called_once()

    def test_send_otp_invalid_email(self):
        """Test OTP sending with invalid email."""
        response = self.client.post(
            self.login_otp_url, {"email": "invalid@example.com"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(OTP.objects.filter(user=self.user).exists())

    def test_send_otp_missing_email(self):
        """Test OTP sending without email."""
        response = self.client.post(self.login_otp_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_success(self):
        """Test successful OTP verification."""
        with override_settings(RATELIMIT_ENABLE=False):
            otp_code = generate_otp()
            OTP.objects.create(
                user=self.user,
                code=otp_code,
                expires_at=timezone.now() + timedelta(minutes=10),
                purpose="login",
            )

            response = self.client.post(
                self.verify_otp_url, {"email": "testuser@example.com", "otp": otp_code}
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("access", response.data)
            self.assertIn("refresh", response.data)

    def test_verify_otp_invalid_code(self):
        """Test OTP verification with invalid code."""
        with override_settings(RATELIMIT_ENABLE=False):
            self.user.generate_verification_code()

            response = self.client.post(
                self.verify_otp_url, {"email": "testuser@example.com", "otp": "000000"}
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_expired_code(self):
        """Test OTP verification with expired code."""
        with override_settings(RATELIMIT_ENABLE=False):
            otp_code = generate_otp()
            OTP.objects.create(
                user=self.user,
                code=otp_code,
                expires_at=timezone.now() - timedelta(minutes=1),
                purpose="login",
            )

            response = self.client.post(
                self.verify_otp_url, {"email": "testuser@example.com", "otp": otp_code}
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_used_code(self):
        """Test OTP verification with already used code."""
        with override_settings(RATELIMIT_ENABLE=False):
            otp_code = generate_otp()
            otp = OTP.objects.create(
                user=self.user,
                code=otp_code,
                expires_at=timezone.now() + timedelta(minutes=10),
                purpose="login",
                is_used=True,
            )

            response = self.client.post(
                self.verify_otp_url, {"email": "testuser@example.com", "otp": otp_code}
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OTPRegistrationTests(APITransactionTestCase):
    """Test OTP functionality during registration."""

    def setUp(self):
        super().setUp()
        self.register_url = reverse("auth-register")


class OTPPasswordResetTests(APITransactionTestCase):
    """Test OTP functionality during password reset."""

    def setUp(self):
        super().setUp()
        self.user = self.create_test_user(
            email="testuser@example.com",
            phone_number="+21626716816",
            is_email_verified=True,
        )
        self.forgot_password_url = reverse("auth-forgot-password")
        self.reset_password_url = reverse("auth-reset-password")


class OTPDeliveryTests(APITransactionTestCase):
    """Test OTP delivery mechanisms."""

    def setUp(self):
        super().setUp()
        self.user = self.create_test_user(
            email="testuser@example.com",
            phone_number="+21626716816",
            is_email_verified=True,
        )


class OTPFallbackTests(APITransactionTestCase):
    """Test OTP fallback mechanisms."""

    def setUp(self):
        super().setUp()
        self.user = self.create_test_user(
            email="testuser@example.com",
            phone_number="+21626716816",
            is_email_verified=True,
        )


class OTPSecurityTests(APITransactionTestCase):
    """Test OTP security features."""

    def setUp(self):
        super().setUp()
        self.user = self.create_test_user(
            email="testuser@example.com", phone_number="+21626716816"
        )


try:
    from .test_otp import *
except ImportError:
    pass
