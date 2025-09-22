from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from unittest.mock import patch

from apps.accounts.auth.serializers.register import RegisterSerializer

User = get_user_model()


class RegisterSerializerTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.request = self.factory.get("/")
        self.context = {"request": self.request}

        self.existing_user = User.objects.create_user(
            email="existing@example.com",
            password="password123",
            fullname="Existing User",
            username="existinguser",
            phone_number="+4000000000",
        )

        self.existing_user.save()

    def tearDown(self):
        User.objects.all().delete()

    @patch("apps.accounts.auth.serializers.register.send_activation_email")
    def test_register_serializer_lowercase_email(self, mock_send_email):
        """Test that the register serializer converts emails to lowercase."""

        User.objects.filter(email__iexact="new_user@example.com").delete()

        data = {
            "email": "NEW_USER@EXAMPLE.COM",
            "password": "password123",
            "fullname": "New User",
            "phone_number": "+4010203040",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        self.assertEqual(user.email, "new_user@example.com")

        self.assertTrue(User.objects.filter(email="new_user@example.com").exists())

        data = {
            "email": "new_user@EXAMPLE.com",
            "password": "password123",
            "fullname": "Another User",
            "phone_number": "+4020304050",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_register_serializer_existing_email(self):
        """Test that the register serializer rejects existing emails regardless of case."""

        self.existing_user.email = "existing@example.com"
        self.existing_user.save()

        self.assertTrue(User.objects.filter(email="existing@example.com").exists())

        data = {
            "email": "EXISTING@EXAMPLE.COM",
            "password": "password123",
            "fullname": "New User",
            "phone_number": "+4030405060",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

        data = {
            "email": "ExIsTiNg@eXaMpLe.CoM",
            "password": "password123",
            "fullname": "New User",
            "phone_number": "+4040506070",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    @patch("apps.accounts.auth.serializers.register.send_activation_email")
    def test_register_serializer_required_phone_number(self, mock_send_email):
        """Test that phone_number field is required and properly saved."""

        data = {
            "email": "phone_test@example.com",
            "password": "password123",
            "fullname": "Phone Number User",
            "phone_number": "1234567890",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.phone_number, "1234567890")

    def test_register_serializer_phone_number_required(self):
        """Test that registration fails without phone_number."""

        data = {
            "email": "nophone@example.com",
            "password": "password123",
            "fullname": "No Phone User",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)
        self.assertEqual(serializer.errors["phone_number"][0].code, "required")
