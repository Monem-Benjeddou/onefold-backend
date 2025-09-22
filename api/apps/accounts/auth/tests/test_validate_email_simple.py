"""
Simple test for email validation endpoint to verify all verification fields are set.
"""

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.user.models import VerificationCode

User = get_user_model()


class SimpleEmailValidationTest(TransactionTestCase):
    """Simple test that email validation sets all four verification fields to True."""

    def test_validate_email_sets_all_verification_fields(self):
        """Test that email validation sets all four verification fields to True."""
        client = APIClient()
        
        
        user = User.objects.create_user(
            email="simpletest@example.com",
            password="testpass123",
            fullname="Simple Test User",
            username="simpletest",
            is_active=False,
            is_email_verified=False,
            is_phone_verified=False,
            is_verified=False,
        )

        
        VerificationCode.objects.create(user=user, code="987654")

        
        data = {"code": "987654", "email": "simpletest@example.com"}
        response = client.post("/api/v1/auth/validate-email/", data)

        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        
        user.refresh_from_db()
        self.assertTrue(user.is_active, "is_active should be True")
        self.assertTrue(user.is_email_verified, "is_email_verified should be True")
        self.assertTrue(user.is_phone_verified, "is_phone_verified should be True")
        self.assertTrue(user.is_verified, "is_verified should be True")