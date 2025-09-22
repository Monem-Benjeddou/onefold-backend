from django.test import TestCase, override_settings
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from apps.accounts.auth.serializers.logout import LogoutSerializer

User = get_user_model()


class LogoutSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            fullname="Test User",
            username="testuser",
        )
        self.refresh_token = RefreshToken.for_user(self.user)

    def test_valid_refresh_token(self):
        """Test that valid refresh token passes serializer validation"""
        data = {"refresh": str(self.refresh_token)}
        serializer = LogoutSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["refresh"], str(self.refresh_token))

    def test_missing_refresh_token(self):
        """Test that missing refresh token fails validation"""
        data = {}
        serializer = LogoutSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("refresh", serializer.errors)

        self.assertTrue(len(serializer.errors["refresh"]) > 0)

    def test_empty_refresh_token(self):
        """Test that empty refresh token fails validation"""
        data = {"refresh": ""}
        serializer = LogoutSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("refresh", serializer.errors)

        self.assertTrue(len(serializer.errors["refresh"]) > 0)

    def test_null_refresh_token(self):
        """Test that null refresh token fails validation"""
        data = {"refresh": None}
        serializer = LogoutSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("refresh", serializer.errors)

    def test_whitespace_refresh_token(self):
        """Test that whitespace-only refresh token fails validation"""
        data = {"refresh": "   "}
        serializer = LogoutSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("refresh", serializer.errors)

    @override_settings(LANGUAGE_CODE="en-US")
    def test_serializer_help_text(self):
        """Test that serializer provides helpful field descriptions"""
        serializer = LogoutSerializer()
        refresh_field = serializer.fields["refresh"]

        self.assertIn("refresh token", refresh_field.help_text.lower())

    def test_serializer_error_messages(self):
        """Test that serializer has custom error messages"""
        serializer = LogoutSerializer()
        refresh_field = serializer.fields["refresh"]

        self.assertIn("required", refresh_field.error_messages)
        self.assertIn("blank", refresh_field.error_messages)

        self.assertTrue(len(refresh_field.error_messages["required"]) > 0)

    def test_serializer_with_extra_fields(self):
        """Test that serializer ignores extra fields"""
        data = {"refresh": str(self.refresh_token), "extra_field": "should_be_ignored"}
        serializer = LogoutSerializer(data=data)

        self.assertTrue(serializer.is_valid())

        self.assertNotIn("extra_field", serializer.validated_data)
        self.assertEqual(serializer.validated_data["refresh"], str(self.refresh_token))

    def test_serializer_field_type(self):
        """Test that refresh field is CharField"""
        serializer = LogoutSerializer()
        refresh_field = serializer.fields["refresh"]

        self.assertIsInstance(refresh_field, serializers.CharField)

    def test_invalid_token_format_still_passes_serializer(self):
        """Test that invalid token format passes serializer validation but would fail in view"""

        data = {"refresh": "invalid_token_format"}
        serializer = LogoutSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["refresh"], "invalid_token_format")
