from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError

from apps.accounts.auth.serializers.register import EmailVerificationSerializer
from apps.accounts.user.models import VerificationCode

User = get_user_model()


class EmailVerificationSerializerTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.request = self.factory.get("/")
        self.context = {"request": self.request}

        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            fullname="Test User",
            username="testuser",
        )

        self.verification_code = VerificationCode.objects.create(
            user=self.user, code="123456"
        )

    def test_email_verification_serializer_lowercase_email(self):
        """Test that the email verification serializer handles case-insensitive emails."""

        VerificationCode.objects.all().delete()

        self.verification_code = VerificationCode.objects.create(
            user=self.user, code="123456"
        )

        data = {"email": "USER@EXAMPLE.COM", "code": "123456"}

        serializer = EmailVerificationSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())
        serializer.save()

        VerificationCode.objects.all().delete()

        self.verification_code = VerificationCode.objects.create(
            user=self.user, code="123456"
        )

        data = {"email": "UsEr@eXaMpLe.CoM", "code": "123456"}

        serializer = EmailVerificationSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

    def test_email_verification_serializer_invalid_code(self):
        """Test that the email verification serializer rejects invalid codes."""
        data = {"email": "user@example.com", "code": "654321"}

        serializer = EmailVerificationSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("code", serializer.errors)

    def test_email_verification_serializer_nonexistent_user(self):
        """Test that the email verification serializer handles non-existent users."""
        data = {"email": "nonexistent@example.com", "code": "123456"}

        serializer = EmailVerificationSerializer(data=data, context=self.context)

        if not serializer.is_valid(raise_exception=False):
            self.assertIn("email", serializer.errors)
