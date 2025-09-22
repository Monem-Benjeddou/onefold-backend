from typing import Any
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITransactionTestCase
from django.utils import timezone
from django.test import override_settings
from apps.accounts.user.models import User
from apps.accounts.auth.models import OTP
from apps.accounts.auth.utils import generate_otp
from core.utilities import tprint


class OTPLoginTests(APITransactionTestCase):
    def setUp(self):
        self.user = User.objects.create(
            email="testuser@example.com",
            username="testuser",
            password="testpassword",
            phone_number="+21626716816",
            is_email_verified=True,
        )
        self.user.set_password("testpassword")
        self.user.save()
        self.login_otp_url = reverse("auth-login-otp")
        self.verify_otp_url = reverse("auth-verify-otp")

    @patch("core.tasks.sms.send_sms_task.delay")
    def test_send_otp_success(self, mock_sms_task):
        mock_sms_task.return_value = MagicMock()

        response: Any = self.client.post(
            self.login_otp_url, {"email": "testuser@example.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(OTP.objects.filter(user=self.user).exists())

    def test_send_otp_invalid_email(self):
        response: Any = self.client.post(
            self.login_otp_url, {"email": "invalid@example.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_success(self):
        with override_settings(RATELIMIT_ENABLE=False):
            otp_code = generate_otp()
            OTP.objects.create(
                user=self.user,
                code=otp_code,
                expires_at=timezone.now() + timezone.timedelta(minutes=10),
            )

            response: Any = self.client.post(
                self.verify_otp_url,
                {"email": "testuser@example.com", "otp": otp_code},
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("access", response.data)
            self.assertIn("refresh", response.data)
            self.assertIn("user", response.data)

    def test_verify_otp_invalid_otp(self):
        otp_code = generate_otp()
        OTP.objects.create(
            user=self.user,
            code=otp_code,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )

        response: Any = self.client.post(
            self.verify_otp_url,
            {"email": "testuser@example.com", "otp": "wrongotp"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_expired_otp(self):
        otp_code = generate_otp()
        OTP.objects.create(
            user=self.user,
            code=otp_code,
            expires_at=timezone.now() - timezone.timedelta(minutes=1),
        )

        response: Any = self.client.post(
            self.verify_otp_url,
            {"email": "testuser@example.com", "otp": otp_code},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_invalid_email(self):
        otp_code = generate_otp()
        OTP.objects.create(
            user=self.user,
            code=otp_code,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )

        response: Any = self.client.post(
            self.verify_otp_url,
            {"email": "invalid@example.com", "otp": otp_code},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = response.json()
        expected_message = "User with this email does not exist."

        self.assertTrue(
            response_data == {"email": [expected_message]}
            or response_data == {"error": {"email": [expected_message]}}
        )
