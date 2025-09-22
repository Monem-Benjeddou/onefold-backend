"""
Test cases for User model's send_otp method.

Tests cover:
1. send_otp method functionality
2. Integration with OTPDeliveryService
3. OTP model interactions
4. Error handling and edge cases
5. Different OTP types
"""

from unittest.mock import patch, Mock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.accounts.auth.models import OTP

User = get_user_model()


class UserSendOTPMethodTestCase(TestCase):
    """Test cases for User model's send_otp method."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            fullname="Test User",
            phone_number="+1234567890",
            username="testuser",
        )

    def tearDown(self):
        User.objects.all().delete()
        OTP.objects.all().delete()

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_send_otp_with_existing_otp(self, mock_delivery_service):
        """Test send_otp method when user has an existing OTP."""

        otp = OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        mock_delivery_service.return_value = True

        result = self.user.send_otp("login")

        self.assertTrue(result)
        mock_delivery_service.assert_called_once_with(self.user, "123456", "login")

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_send_otp_without_existing_otp(self, mock_delivery_service):
        """Test send_otp method when user has no existing OTP."""
        mock_delivery_service.return_value = True

        result = self.user.send_otp("login")

        self.assertFalse(result)
        mock_delivery_service.assert_not_called()

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_send_otp_gets_latest_otp(self, mock_delivery_service):
        """Test that send_otp gets the latest OTP when multiple exist."""

        old_otp = OTP.objects.create(
            user=self.user,
            code="111111",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        old_otp.created = timezone.now() - timedelta(seconds=1)
        old_otp.save()

        new_otp = OTP.objects.create(
            user=self.user,
            code="222222",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        mock_delivery_service.return_value = True

        result = self.user.send_otp("login")

        self.assertTrue(result)

        mock_delivery_service.assert_called_once_with(self.user, "222222", "login")

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_send_otp_login_type(self, mock_delivery_service):
        """Test send_otp with login type."""
        OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        mock_delivery_service.return_value = True

        result = self.user.send_otp("login")

        self.assertTrue(result)
        mock_delivery_service.assert_called_once_with(self.user, "123456", "login")

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_send_otp_password_reset_type(self, mock_delivery_service):
        """Test send_otp with password_reset type."""
        OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        mock_delivery_service.return_value = True

        result = self.user.send_otp("password_reset")

        self.assertTrue(result)
        mock_delivery_service.assert_called_once_with(
            self.user, "123456", "password_reset"
        )

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_send_otp_verification_type(self, mock_delivery_service):
        """Test send_otp with verification type."""
        OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        mock_delivery_service.return_value = True

        result = self.user.send_otp("verification")

        self.assertTrue(result)
        mock_delivery_service.assert_called_once_with(
            self.user, "123456", "verification"
        )

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_send_otp_default_login_type(self, mock_delivery_service):
        """Test send_otp with default type (no parameter)."""
        OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        mock_delivery_service.return_value = True

        result = self.user.send_otp()

        self.assertTrue(result)
        mock_delivery_service.assert_called_once_with(self.user, "123456", "login")

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_send_otp_delivery_service_failure(self, mock_delivery_service):
        """Test send_otp when delivery service fails."""
        OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        mock_delivery_service.return_value = False

        result = self.user.send_otp("login")

        self.assertFalse(result)
        mock_delivery_service.assert_called_once()

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_send_otp_delivery_service_exception(self, mock_delivery_service):
        """Test send_otp when delivery service raises exception."""
        OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        mock_delivery_service.side_effect = Exception("Delivery failed")

        result = self.user.send_otp("login")

        self.assertFalse(result)

    def test_send_otp_no_otp_exists(self):
        """Test send_otp when no OTP exists for user."""

        result = self.user.send_otp("login")

        self.assertFalse(result)

    @override_settings(OTP_DELIVERY_METHOD="sms")
    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_send_otp_with_sms_delivery(self, mock_delivery_service):
        """Test send_otp with SMS delivery method configured."""
        OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        mock_delivery_service.return_value = True

        result = self.user.send_otp("login")

        self.assertTrue(result)

        mock_delivery_service.assert_called_once_with(self.user, "123456", "login")

    @override_settings(OTP_DELIVERY_METHOD="email")
    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_send_otp_with_email_delivery(self, mock_delivery_service):
        """Test send_otp with email delivery method configured."""
        OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        mock_delivery_service.return_value = True

        result = self.user.send_otp("login")

        self.assertTrue(result)
        mock_delivery_service.assert_called_once_with(self.user, "123456", "login")

    def test_send_otp_user_without_phone(self):
        """Test send_otp for user without phone number."""
        user_no_phone = User.objects.create_user(
            email="nophone@example.com",
            password="password123",
            fullname="No Phone User",
            username="nophoneuser",
        )

        OTP.objects.create(
            user=user_no_phone,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
        ) as mock_delivery:
            mock_delivery.return_value = True

            result = user_no_phone.send_otp("login")

            self.assertTrue(result)
            mock_delivery.assert_called_once_with(user_no_phone, "123456", "login")

    def test_send_otp_user_without_email(self):
        """Test send_otp for user without email."""
        user_no_email = User.objects.create_user(
            email="",
            password="password123",
            fullname="No Email User",
            phone_number="+1111111111",
            username="noemailuser",
        )

        OTP.objects.create(
            user=user_no_email,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
        ) as mock_delivery:
            mock_delivery.return_value = True

            result = user_no_email.send_otp("login")

            self.assertTrue(result)
            mock_delivery.assert_called_once_with(user_no_email, "123456", "login")

    def test_send_otp_with_different_otp_codes(self):
        """Test send_otp with various OTP code formats."""
        test_codes = ["123456", "000000", "999999", "654321"]

        for code in test_codes:
            with self.subTest(code=code):

                OTP.objects.filter(user=self.user).delete()

                OTP.objects.create(
                    user=self.user,
                    code=code,
                    expires_at=timezone.now() + timedelta(minutes=10),
                )

                with patch(
                    "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
                ) as mock_delivery:
                    mock_delivery.return_value = True

                    result = self.user.send_otp("login")

                    self.assertTrue(result)
                    mock_delivery.assert_called_once_with(self.user, code, "login")

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
    )
    def test_send_otp_with_expired_otp(self, mock_delivery_service):
        """Test send_otp with expired OTP (should still send)."""

        expired_otp = OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() - timedelta(minutes=5),
        )

        mock_delivery_service.return_value = True

        result = self.user.send_otp("login")

        self.assertTrue(result)
        mock_delivery_service.assert_called_once_with(self.user, "123456", "login")

    def test_send_otp_integration_with_generate_code(self):
        """Test integration between generate_verification_code and send_otp."""

        code = self.user.generate_verification_code()

        otp = OTP.objects.get(user=self.user, code=code)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
        ) as mock_delivery:
            mock_delivery.return_value = True

            result = self.user.send_otp("login")

            self.assertTrue(result)
            mock_delivery.assert_called_once_with(self.user, code, "login")

    def test_send_otp_multiple_users_different_otps(self):
        """Test send_otp works correctly with multiple users."""
        user2 = User.objects.create_user(
            email="user2@example.com",
            password="password123",
            fullname="User Two",
            phone_number="+9876543210",
            username="user2",
        )

        OTP.objects.create(
            user=self.user,
            code="111111",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        OTP.objects.create(
            user=user2, code="222222", expires_at=timezone.now() + timedelta(minutes=10)
        )

        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
        ) as mock_delivery:
            mock_delivery.return_value = True

            result1 = self.user.send_otp("login")
            self.assertTrue(result1)

            result2 = user2.send_otp("login")
            self.assertTrue(result2)

            calls = mock_delivery.call_args_list
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0][0], (self.user, "111111", "login"))
            self.assertEqual(calls[1][0], (user2, "222222", "login"))

    def test_send_otp_return_type(self):
        """Test that send_otp returns boolean."""
        OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
        ) as mock_delivery:
            mock_delivery.return_value = True
            result = self.user.send_otp("login")
            self.assertIsInstance(result, bool)
            self.assertTrue(result)

            mock_delivery.return_value = False
            result = self.user.send_otp("login")
            self.assertIsInstance(result, bool)
            self.assertFalse(result)

    def test_send_otp_method_exists(self):
        """Test that send_otp method exists and is callable."""
        self.assertTrue(hasattr(self.user, "send_otp"))
        self.assertTrue(callable(getattr(self.user, "send_otp")))

    def test_send_otp_accepts_otp_type_parameter(self):
        """Test that send_otp method accepts otp_type parameter."""
        OTP.objects.create(
            user=self.user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        with patch(
            "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_otp"
        ) as mock_delivery:
            mock_delivery.return_value = True

            result = self.user.send_otp(otp_type="password_reset")
            self.assertTrue(result)

            result = self.user.send_otp("verification")
            self.assertTrue(result)

            calls = mock_delivery.call_args_list
            self.assertEqual(calls[0][0][2], "password_reset")
            self.assertEqual(calls[1][0][2], "verification")
