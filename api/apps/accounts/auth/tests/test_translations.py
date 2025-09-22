from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.test import override_settings
from unittest.mock import patch
from typing import Union
from django.utils.translation import gettext_lazy as _

from core.utilities import tprint

User = get_user_model()


class AuthenticationTranslationTest(APITestCase):
    def setUp(self):
        self.client.defaults["HTTP_ACCEPT_LANGUAGE"] = "ar"

    def test_invalid_login(self):
        with override_settings(RATELIMIT_ENABLE=False):
            url = reverse("auth-login")
            data = {"email": "invalid@example.com", "password": "invalidpassword"}
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEqual(
                response.json(),
                {"error": _("User does not exist.")},
            )

    def test_invalid_refresh_token(self):
        url = reverse("auth-refresh")
        data = {"refresh": "invalidtoken"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {"error": _("Token is invalid or expired")})

    def test_invalid_forgot_password(self):
        url = reverse("auth-forgot-password")
        data = {"email": "invalid@example.com"}
        response = self.client.post(url, data, headers={"HTTP_ACCEPT_LANGUAGE": "ar"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(), {"error": {"email": [_("User does not exist.")]}}
        )

    def test_invalid_reset_password(self):
        url = reverse("auth-reset-password")
        data = {"token": "invalidtoken", "password": "newpassword"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"error": _("Invalid or expired token")})

    def test_invalid_resend_verification_code(self):
        url = reverse("auth-resend-verification-code")
        data = {"email": "invalid@example.com"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(), {"error": {"email": [_("User does not exist.")]}}
        )
