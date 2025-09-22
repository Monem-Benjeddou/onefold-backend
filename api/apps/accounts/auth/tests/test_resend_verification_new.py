import pytest
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.apps import apps
from django.utils import timezone
from unittest.mock import patch, MagicMock
from datetime import timedelta

from apps.accounts.auth.models import OTP
from apps.accounts.user.models import VerificationCode

User = get_user_model()


class ResendVerificationCodeTest(APITestCase):
    """Test suite for the resend verification code functionality."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            fullname="Test User",
            username="testuser",
            phone_number="+1234567890",
        )
        self.user.save()

        try:
            self.test_country = apps.get_model("countries", "Country").objects.create(
                name="Test Country", iso2="TC", iso3="TCY"
            )
        except Exception:

            pass

        self.resend_url = "/api/v1/auth/resend-verification-code/"

    def test_get_or_generate_verification_code_creates_new_when_none_exists(self):
        """Test that get_or_generate_verification_code creates a new OTP when none exists."""

        OTP.objects.filter(user=self.user, purpose="registration").delete()

        otp_code = self.user.get_or_generate_verification_code("registration")

        otp = OTP.objects.get(user=self.user, purpose="registration")
        self.assertEqual(otp.code, otp_code)
        self.assertFalse(otp.is_used)
        self.assertTrue(otp.is_valid())

    def test_get_or_generate_verification_code_reuses_valid_existing(self):
        """Test that get_or_generate_verification_code reuses existing valid OTP."""

        existing_otp = OTP.objects.create(
            user=self.user,
            code="123456",
            purpose="registration",
            is_used=False,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        otp_code = self.user.get_or_generate_verification_code("registration")

        self.assertEqual(otp_code, "123456")

        otp_count = OTP.objects.filter(user=self.user, purpose="registration").count()
        self.assertEqual(otp_count, 1)

    def test_get_or_generate_verification_code_creates_new_when_existing_expired(self):
        """Test that get_or_generate_verification_code creates new OTP when existing is expired."""

        expired_otp = OTP.objects.create(
            user=self.user,
            code="123456",
            purpose="registration",
            is_used=False,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        otp_code = self.user.get_or_generate_verification_code("registration")

        self.assertNotEqual(otp_code, "123456")

        otp_count = OTP.objects.filter(user=self.user, purpose="registration").count()
        self.assertEqual(otp_count, 1)

        new_otp = OTP.objects.get(user=self.user, purpose="registration")
        self.assertEqual(new_otp.code, otp_code)
        self.assertTrue(new_otp.is_valid())

    def test_get_or_generate_verification_code_creates_new_when_existing_used(self):
        """Test that get_or_generate_verification_code creates new OTP when existing is used."""

        used_otp = OTP.objects.create(
            user=self.user,
            code="123456",
            purpose="registration",
            is_used=True,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        otp_code = self.user.get_or_generate_verification_code("registration")

        self.assertNotEqual(otp_code, "123456")

        otp_count = OTP.objects.filter(user=self.user, purpose="registration").count()
        self.assertEqual(otp_count, 1)

        new_otp = OTP.objects.get(user=self.user, purpose="registration")
        self.assertEqual(new_otp.code, otp_code)
        self.assertTrue(new_otp.is_valid())

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_sms_otp"
    )
    def test_resend_sms_verification_reuses_existing_valid_otp(self, mock_send_sms):
        """Test that resending SMS verification reuses existing valid OTP."""
        mock_send_sms.return_value = True

        existing_otp = OTP.objects.create(
            user=self.user,
            code="123456",
            purpose="registration",
            is_used=False,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        response1 = self.client.post(
            self.resend_url, {"phone_number": self.user.phone_number}
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(
            self.resend_url, {"phone_number": self.user.phone_number}
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        self.assertEqual(mock_send_sms.call_count, 2)
        first_call_code = mock_send_sms.call_args_list[0][0][1]
        second_call_code = mock_send_sms.call_args_list[1][0][1]
        self.assertEqual(first_call_code, second_call_code)
        self.assertEqual(first_call_code, "123456")

        otp_count = OTP.objects.filter(user=self.user, purpose="registration").count()
        self.assertEqual(otp_count, 1)

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_email_otp"
    )
    def test_resend_email_verification_reuses_existing_valid_otp(self, mock_send_email):
        """Test that resending email verification reuses existing valid OTP."""
        mock_send_email.return_value = True

        existing_otp = OTP.objects.create(
            user=self.user,
            code="789012",
            purpose="registration",
            is_used=False,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        response1 = self.client.post(self.resend_url, {"email": self.user.email})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(self.resend_url, {"email": self.user.email})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        self.assertEqual(mock_send_email.call_count, 2)
        first_call_code = mock_send_email.call_args_list[0][0][1]
        second_call_code = mock_send_email.call_args_list[1][0][1]
        self.assertEqual(first_call_code, second_call_code)
        self.assertEqual(first_call_code, "789012")

        otp_count = OTP.objects.filter(user=self.user, purpose="registration").count()
        self.assertEqual(otp_count, 1)

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_sms_otp"
    )
    def test_resend_creates_new_when_no_existing_otp(self, mock_send_sms):
        """Test that resend creates new OTP when none exists."""
        mock_send_sms.return_value = True

        OTP.objects.filter(user=self.user, purpose="registration").delete()

        response = self.client.post(
            self.resend_url, {"phone_number": self.user.phone_number}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        otp = OTP.objects.get(user=self.user, purpose="registration")
        self.assertFalse(otp.is_used)
        self.assertTrue(otp.is_valid())

        mock_send_sms.assert_called_once()
        sent_code = mock_send_sms.call_args[0][1]
        self.assertEqual(sent_code, otp.code)

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_sms_otp"
    )
    def test_resend_creates_new_when_existing_expired(self, mock_send_sms):
        """Test that resend creates new OTP when existing is expired."""
        mock_send_sms.return_value = True

        expired_otp = OTP.objects.create(
            user=self.user,
            code="999999",
            purpose="registration",
            is_used=False,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        response = self.client.post(
            self.resend_url, {"phone_number": self.user.phone_number}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_otp = OTP.objects.get(user=self.user, purpose="registration")
        self.assertNotEqual(new_otp.code, "999999")
        self.assertTrue(new_otp.is_valid())

        sent_code = mock_send_sms.call_args[0][1]
        self.assertEqual(sent_code, new_otp.code)

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_sms_otp"
    )
    def test_resend_fails_when_sms_delivery_fails(self, mock_send_sms):
        """Test that resend fails gracefully when SMS delivery fails."""
        mock_send_sms.return_value = False

        response = self.client.post(
            self.resend_url, {"phone_number": self.user.phone_number}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("Failed to send verification code via SMS", str(response.data))

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_email_otp"
    )
    def test_resend_fails_when_email_delivery_fails(self, mock_send_email):
        """Test that resend fails gracefully when email delivery fails."""
        mock_send_email.return_value = False

        response = self.client.post(self.resend_url, {"email": self.user.email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("Failed to send verification code via email", str(response.data))

    def test_resend_requires_existing_user(self):
        """Test that resend fails for non-existent users."""
        response = self.client.post(
            self.resend_url, {"email": "nonexistent@example.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User does not exist", str(response.data))

    def test_resend_requires_email_or_phone(self):
        """Test that resend requires either email or phone number."""
        response = self.client.post(self.resend_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Either email or phone number must be provided", str(response.data)
        )

    def test_resend_cannot_have_both_email_and_phone(self):
        """Test that resend cannot accept both email and phone number."""
        response = self.client.post(
            self.resend_url,
            {"email": self.user.email, "phone_number": self.user.phone_number},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Please provide either email or phone number, not both", str(response.data)
        )

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_sms_otp"
    )
    def test_multiple_resends_same_session_reuse_otp(self, mock_send_sms):
        """Test that multiple resends in the same session reuse the same valid OTP."""
        mock_send_sms.return_value = True

        response1 = self.client.post(
            self.resend_url, {"phone_number": self.user.phone_number}
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        first_otp = OTP.objects.get(user=self.user, purpose="registration")

        response2 = self.client.post(
            self.resend_url, {"phone_number": self.user.phone_number}
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        response3 = self.client.post(
            self.resend_url, {"phone_number": self.user.phone_number}
        )
        self.assertEqual(response3.status_code, status.HTTP_200_OK)

        otp_count = OTP.objects.filter(user=self.user, purpose="registration").count()
        self.assertEqual(otp_count, 1)

        current_otp = OTP.objects.get(user=self.user, purpose="registration")
        self.assertEqual(current_otp.code, first_otp.code)

        self.assertEqual(mock_send_sms.call_count, 3)
        for call in mock_send_sms.call_args_list:
            sent_code = call[0][1]
            self.assertEqual(sent_code, first_otp.code)


class ResendVerificationCodeIntegrationTest(APITestCase):
    """Integration tests for the complete verification flow."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            fullname="Test User",
            username="testuser",
            phone_number="+1234567890",
        )
        self.resend_url = "/api/v1/auth/resend-verification-code/"
        self.verify_url = "/api/v1/auth/verify-registration-otp/"

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_email_otp"
    )
    def test_complete_flow_resend_then_verify_with_first_otp(self, mock_send_email):
        """Test the complete flow: resend verification and verify with the first OTP."""
        mock_send_email.return_value = True

        initial_otp_code = self.user.get_or_generate_verification_code("registration")

        resend_response = self.client.post(self.resend_url, {"email": self.user.email})
        self.assertEqual(resend_response.status_code, status.HTTP_200_OK)

        verify_response = self.client.post(
            self.verify_url, {"email": self.user.email, "otp": initial_otp_code}
        )

        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        otp = OTP.objects.get(user=self.user, purpose="registration")
        self.assertTrue(otp.is_used)

    @patch(
        "apps.accounts.auth.services.otp_delivery_service.OTPDeliveryService.send_email_otp"
    )
    def test_resend_after_expiry_creates_new_otp(self, mock_send_email):
        """Test that resend after OTP expiry creates a new OTP."""
        mock_send_email.return_value = True

        expired_otp = OTP.objects.create(
            user=self.user,
            code="111111",
            purpose="registration",
            is_used=False,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        resend_response = self.client.post(self.resend_url, {"email": self.user.email})
        self.assertEqual(resend_response.status_code, status.HTTP_200_OK)

        new_otp = OTP.objects.get(user=self.user, purpose="registration")
        self.assertNotEqual(new_otp.code, "111111")
        self.assertTrue(new_otp.is_valid())

        verify_response = self.client.post(
            self.verify_url, {"email": self.user.email, "otp": new_otp.code}
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
