"""
Comprehensive tests for email validation endpoint verification status updates.

This module tests that email validation properly updates all user verification status fields:
- is_email_verified
- is_phone_verified 
- is_verified (for blue check verification)
- is_active
"""

import pytest
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.user.models import VerificationCode

User = get_user_model()


class EmailValidationVerificationTest(TransactionTestCase):
    """Test that email validation correctly updates all user verification status fields."""

    def setUp(self):
        self.client = APIClient()
        self.validate_url = "/api/v1/auth/validate-email/"

        
        self.inactive_user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            fullname="Test User",
            username="testuser",
            phone_number="+1234567890",
            is_active=False,
            is_email_verified=False,
            is_phone_verified=False,
            is_verified=False,
        )

        
        self.verification_code = VerificationCode.objects.create(
            user=self.inactive_user,
            code="123456"
        )

    def test_validate_email_sets_all_verification_fields(self):
        """Test that email validation sets all four verification fields to True."""
        data = {"code": "123456", "email": "test@example.com"}

        response = self.client.post(self.validate_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        
        self.assertIn("message", response.data)
        self.assertIn("user", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("access", response.data)

        
        self.inactive_user.refresh_from_db()

        
        self.assertTrue(self.inactive_user.is_active)
        self.assertTrue(self.inactive_user.is_email_verified)
        self.assertTrue(self.inactive_user.is_phone_verified)
        self.assertTrue(self.inactive_user.is_verified)

        
        self.assertFalse(
            VerificationCode.objects.filter(code="123456").exists()
        )

    def test_validate_email_invalid_code(self):
        """Test email validation with invalid verification code."""
        data = {"code": "invalidcode"}

        response = self.client.post(self.validate_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        
        self.inactive_user.refresh_from_db()
        self.assertFalse(self.inactive_user.is_active)
        self.assertFalse(self.inactive_user.is_email_verified)
        self.assertFalse(self.inactive_user.is_phone_verified)
        self.assertFalse(self.inactive_user.is_verified)

    def test_validate_email_missing_code(self):
        """Test email validation without providing code."""
        data = {}

        response = self.client.post(self.validate_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        
        self.inactive_user.refresh_from_db()
        self.assertFalse(self.inactive_user.is_active)
        self.assertFalse(self.inactive_user.is_email_verified)
        self.assertFalse(self.inactive_user.is_phone_verified)
        self.assertFalse(self.inactive_user.is_verified)

    def test_validate_email_enables_login(self):
        """Test that after successful email validation, user can login."""
        
        data = {"code": "123456", "email": "test@example.com"}
        response = self.client.post(self.validate_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        
        login_data = {"email": "test@example.com", "password": "testpass123"}
        login_response = self.client.post("/api/v1/auth/login/", login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)
        self.assertIn("user", login_response.data)

    def test_validate_email_already_verified_user(self):
        """Test email validation for a user who is already verified."""
        
        verified_user = User.objects.create_user(
            email="verified@example.com",
            password="testpass123",
            fullname="Verified User",
            username="verified",
            is_active=True,
            is_email_verified=True,
            is_phone_verified=True,
            is_verified=True,
        )

        
        verification_code = VerificationCode.objects.create(
            user=verified_user,
            code="789012"
        )

        data = {"code": "789012", "email": "verified@example.com"}
        response = self.client.post(self.validate_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        
        verified_user.refresh_from_db()
        self.assertTrue(verified_user.is_active)
        self.assertTrue(verified_user.is_email_verified)
        self.assertTrue(verified_user.is_phone_verified)
        self.assertTrue(verified_user.is_verified)

    def test_validate_email_user_without_phone(self):
        """Test email validation for user without phone number."""
        
        user_no_phone = User.objects.create_user(
            email="nophone@example.com",
            password="testpass123",
            fullname="No Phone User",
            username="nophone",
            phone_number=None,
            is_active=False,
            is_email_verified=False,
            is_phone_verified=False,
            is_verified=False,
        )

        verification_code = VerificationCode.objects.create(
            user=user_no_phone,
            code="456789"
        )

        data = {"code": "456789", "email": "nophone@example.com"}
        response = self.client.post(self.validate_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        
        user_no_phone.refresh_from_db()
        self.assertTrue(user_no_phone.is_active)
        self.assertTrue(user_no_phone.is_email_verified)
        self.assertTrue(user_no_phone.is_phone_verified)
        self.assertTrue(user_no_phone.is_verified)