from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.auth.serializers.login import LoginSerializer

User = get_user_model()


class LoginSerializerTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            fullname="Test User",
            username="testuser",
        )

        self.request = self.factory.get("/")
        self.request.query_params = {}
        self.context = {"request": self.request}

    def test_login_serializer_case_insensitive_email(self):
        """Test that the login serializer handles case-insensitive emails correctly."""

        data = {"email": "USER@EXAMPLE.COM", "password": "password123"}
        serializer = LoginSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

        data = {"email": "UsEr@eXaMpLe.CoM", "password": "password123"}
        serializer = LoginSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

        data = {"email": "user@example.com", "password": "password123"}
        serializer = LoginSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

    def test_login_serializer_invalid_credentials(self):
        """Test that the login serializer rejects invalid credentials."""
        data = {"email": "user@example.com", "password": "wrongpassword"}
        serializer = LoginSerializer(data=data, context=self.context)

        with self.assertRaises(AuthenticationFailed) as context:
            serializer.is_valid()

        self.assertTrue("Invalid credentials" in str(context.exception))

    def test_login_serializer_nonexistent_user(self):
        """Test that the login serializer rejects non-existent users."""
        data = {"email": "nonexistent@example.com", "password": "password123"}
        serializer = LoginSerializer(data=data, context=self.context)

        with self.assertRaises(AuthenticationFailed) as context:
            serializer.is_valid()

        self.assertTrue("User does not exist" in str(context.exception))
