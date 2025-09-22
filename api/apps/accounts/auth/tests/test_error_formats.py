from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.test import override_settings
from unittest.mock import patch
from typing import Union

from core.utilities import tprint

User = get_user_model()


class AuthErrorsTest(APITestCase):
    def test_invalid_login(self):
        with override_settings(RATELIMIT_ENABLE=False):
            url = reverse("auth-login")
            data = {"email": "invalid@example.com", "password": "invalidpassword"}
            response = self.client.post(url, data)

            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEqual(
                response.json(),
                {"error": "User does not exist."},
            )

    @override_settings(RATELIMIT_ENABLE=False)
    def test_short_password_register(self):
        url = reverse("auth-register")
        data = {"email": "email@email.com", "password": "short"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "password": ["Password must be at least 8 characters long."],
                    "phone_number": ["Phone number is required."],
                }
            },
        )

    @override_settings(RATELIMIT_ENABLE=False)
    def test_invalid_refresh_token(self):
        url = reverse("auth-refresh")
        data = {"refresh": "invalidtoken"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {"error": "Token is invalid or expired"})

    @override_settings(RATELIMIT_ENABLE=False)
    def test_invalid_forgot_password(self):
        url = reverse("auth-forgot-password")
        data = {"email": "invalid@example.com"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"error": {"email": ["User does not exist."]}},
        )

    @override_settings(RATELIMIT_ENABLE=False)
    def test_invalid_reset_password(self):
        url = reverse("auth-reset-password")
        data = {"token": "invalidtoken", "password": "newpassword"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"error": "Invalid or expired token"})

    @override_settings(RATELIMIT_ENABLE=False)
    @patch("core.tasks.send_activation_email")
    def test_invalid_otp(self, mock_send_email):
        user = User.objects.create_user(email="test@example.com", password="password")
        url = "/api/v1/auth/login_otp/"
        data = {"email": "test@example.com"}

        response = self.client.post(url, data)

        self.assertIn(
            response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        )

        if response.status_code == status.HTTP_200_OK:
            url = "/api/v1/auth/verify_otp/"
            data = {"email": "test@example.com", "otp": "invalidotp"}
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                response.json(),
                {
                    "error": {
                        "otp": ["Ensure this field has no more than 8 characters."]
                    }
                },
            )

    @override_settings(RATELIMIT_ENABLE=False)
    def test_invalid_email_verification(self):
        url = reverse("auth-validate-email")
        data = {"code": "123456"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(), {"error": {"email": ["This field is required."]}}
        )

    @override_settings(RATELIMIT_ENABLE=False)
    def test_invalid_resend_verification_code(self):
        url = reverse("auth-resend-verification-code")
        data = {"email": "invalid@example.com"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"error": {"email": ["User does not exist."]}},
        )
