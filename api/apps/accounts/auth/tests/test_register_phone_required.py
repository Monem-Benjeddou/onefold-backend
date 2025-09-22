"""
Test cases for RegisterSerializer with required phone number functionality.

Tests cover:
1. Phone number requirement validation
2. Phone number uniqueness validation
3. User creation with phone number
4. Email and phone uniqueness together
"""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from unittest.mock import patch

from apps.accounts.auth.serializers.register import RegisterSerializer

User = get_user_model()


class RegisterSerializerPhoneRequiredTestCase(TestCase):
    """Test cases for phone number requirement in registration."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.request = self.factory.get("/")
        self.context = {"request": self.request}

        self.existing_user = User.objects.create_user(
            email="existing@example.com",
            password="password123",
            fullname="Existing User",
            phone_number="+1010101010",
            username="existinguser",
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_phone_number_is_required(self):
        """Test that phone number is required for registration."""
        data = {
            "email": "newuser@example.com",
            "password": "password123",
            "fullname": "New User",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)
        self.assertIn(
            "Phone number is required", str(serializer.errors["phone_number"])
        )

    def test_phone_number_empty_string_invalid(self):
        """Test that empty string phone number is invalid."""
        data = {
            "email": "newuser@example.com",
            "password": "password123",
            "fullname": "New User",
            "phone_number": "",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)

    def test_phone_number_uniqueness_validation(self):
        """Test that duplicate phone numbers are rejected."""
        data = {
            "email": "newuser@example.com",
            "password": "password123",
            "fullname": "New User",
            "phone_number": "+1010101010",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)
        self.assertIn(
            "User with this phone number already exists",
            str(serializer.errors["phone_number"]),
        )

    def test_phone_number_uniqueness_different_formats(self):
        """Test that phone number uniqueness works with different formats."""

        data = {
            "email": "newuser@example.com",
            "password": "password123",
            "fullname": "New User",
            "phone_number": "1010101010",
        }

        serializer = RegisterSerializer(data=data, context=self.context)

        self.assertTrue(serializer.is_valid())

    def test_phone_number_max_length_validation(self):
        """Test that phone number length is validated."""
        data = {
            "email": "newuser@example.com",
            "password": "password123",
            "fullname": "New User",
            "phone_number": "1234567890123456",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)
        self.assertIn(
            "cannot exceed 15 characters", str(serializer.errors["phone_number"])
        )

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_successful_registration_with_phone_number(self, mock_sms_task):
        """Test successful user registration with phone number using SMS."""
        mock_sms_task.return_value = True

        data = {
            "email": "newuser@example.com",
            "password": "password123",
            "fullname": "New User",
            "phone_number": "+1020304050",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.fullname, "New User")
        self.assertEqual(user.phone_number, "+1020304050")
        self.assertEqual(user.role, "collector")
        self.assertTrue(User.objects.filter(phone_number="+1020304050").exists())

        mock_sms_task.assert_called_once()

    @patch("apps.accounts.auth.serializers.register.send_activation_email")
    def test_registration_with_international_phone(self, mock_send_email):
        """Test registration with international phone numbers."""
        data = {
            "email": "international@example.com",
            "password": "password123",
            "fullname": "International User",
            "phone_number": "+1030405060",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.phone_number, "+1030405060")

    def test_email_and_phone_both_unique(self):
        """Test that both email and phone number must be unique."""

        data = {
            "email": "existing@example.com",
            "password": "password123",
            "fullname": "New User",
            "phone_number": "+1040506070",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_registration_generates_verification_code(self, mock_sms_task):
        """Test that registration creates an OTP code for SMS verification."""
        mock_sms_task.return_value = True

        data = {
            "email": "verify@example.com",
            "password": "password123",
            "fullname": "Verify User",
            "phone_number": "+1050607080",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        from apps.accounts.auth.models import OTP

        otps = OTP.objects.filter(user=user)
        self.assertTrue(otps.exists())
        self.assertEqual(len(otps.first().code), 6)

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch("apps.accounts.auth.services.otp_delivery_service.send_activation_email")
    def test_registration_uses_email_verification_when_configured(
        self, mock_send_email
    ):
        """Test that registration uses email verification when OTP_DELIVERY_METHOD=email."""
        mock_send_email.delay.return_value = True

        data = {
            "email": "emailverify@example.com",
            "password": "password123",
            "fullname": "Email Verify User",
            "phone_number": "+1060708090",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        
        from apps.accounts.auth.models import OTP

        otps = OTP.objects.filter(user=user)
        self.assertTrue(otps.exists())
        self.assertEqual(otps.first().purpose, "registration")

        
        mock_send_email.delay.assert_called_once()
        call_args = mock_send_email.delay.call_args
        self.assertIn("Welcome to Kolct", call_args[1]["subject"])
        self.assertEqual(call_args[1]["to_email"], "emailverify@example.com")

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch("core.tasks.sms.send_sms_task.delay")
    def test_registration_uses_sms_verification_when_configured(self, mock_sms_task):
        """Test that registration uses SMS verification when OTP_DELIVERY_METHOD=sms."""
        mock_sms_task.return_value = True

        data = {
            "email": "smsverify@example.com",
            "password": "password123",
            "fullname": "SMS Verify User",
            "phone_number": "+1060708090",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        mock_sms_task.assert_called_once()
        call_args = mock_sms_task.call_args[0]
        message, phone_numbers, otp_type = call_args

        self.assertEqual(["+1060708090"], phone_numbers)
        self.assertEqual("registration", otp_type)
        self.assertIn("Welcome to Kolct", message)

    def test_valid_phone_number_formats(self):
        """Test various valid phone number formats."""
        valid_phones = [
            "+1070809010",
            "1080901020",
            "+1090102030",
            "+1100203040",
            "110304050",
            "+123456789012345",
        ]

        for i, phone in enumerate(valid_phones):
            with self.subTest(phone=phone):
                data = {
                    "email": f"test{i}@example.com",
                    "password": "password123",
                    "fullname": f"Test User {i}",
                    "phone_number": phone,
                }

                serializer = RegisterSerializer(data=data, context=self.context)
                if len(phone) <= 15:
                    self.assertTrue(
                        serializer.is_valid(), f"Phone {phone} should be valid"
                    )
                else:
                    self.assertFalse(
                        serializer.is_valid(), f"Phone {phone} should be invalid"
                    )

    def test_serializer_fields_include_phone_number(self):
        """Test that serializer includes phone_number in fields."""
        serializer = RegisterSerializer()
        self.assertIn("phone_number", serializer.Meta.fields)
        self.assertIn("phone_number", serializer.fields)
        self.assertTrue(serializer.fields["phone_number"].required)

    @patch("apps.accounts.auth.serializers.register.send_activation_email")
    def test_phone_number_saved_to_database(self, mock_send_email):
        """Test that phone number is properly saved to the database."""
        data = {
            "email": "dbtest@example.com",
            "password": "password123",
            "fullname": "DB Test User",
            "phone_number": "+1120304050",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        saved_user = User.objects.get(id=user.id)
        self.assertEqual(saved_user.phone_number, "+1120304050")

    def test_case_insensitive_email_validation_with_phone(self):
        """Test email case insensitivity when phone is provided."""
        data = {
            "email": "EXISTING@EXAMPLE.COM",
            "password": "password123",
            "fullname": "New User",
            "phone_number": "+1130405060",
        }

        serializer = RegisterSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertIn(
            "User with this email already exists", str(serializer.errors["email"])
        )
