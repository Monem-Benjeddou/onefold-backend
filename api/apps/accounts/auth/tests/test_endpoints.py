from rest_framework import status
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.apps import apps
from django.test import override_settings

from apps.accounts.auth.models import OTP
from apps.accounts.auth.tests.constants import (
    REGISTER_URL,
    VALIDATE_EMAIL_URL,
    LOGIN_URL,
    REFRESH_URL,
    LOGOUT_URL,
    FORGOT_PASSWORD_URL,
    RESET_PASSWORD_URL,
    RESEND_VERIFICATION_CODE_URL,
    USER_EMAIL,
    INVALID_EMAIL,
    PASSWORD,
    INVALID_PASSWORD,
    INVALID_TOKEN,
    CODE,
    INVALID_CODE,
)
from apps.accounts.user.models import VerificationCode
from core.utilities import tprint


User = get_user_model()

PASSWORD = "testpassword123"
INVALID_PASSWORD = "test"
USER_EMAIL = "test@example.com"
CODE = "123456"

REGISTER_URL = "/api/v1/auth/register/"
VALIDATE_EMAIL_URL = "/api/v1/auth/validate-email/"
LOGIN_URL = "/api/v1/auth/login/"
REFRESH_URL = "/api/v1/auth/refresh/"
LOGOUT_URL = "/api/v1/auth/logout/"
FORGOT_PASSWORD_URL = "/api/v1/auth/forgot-password/"
RESET_PASSWORD_URL = "/api/v1/auth/reset-password/"
RESEND_VERIFICATION_CODE_URL = "/api/v1/auth/resend-verification-code/"
ADMIN_LOGIN_URL = "/api/v1/auth/admin-login/"


class AuthTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email=USER_EMAIL,
            password=PASSWORD,
            fullname="Test User",
            username="testuser",
            phone_number="+1234567892",
        )
        self.user.save()
        self.refresh = str(RefreshToken.for_user(self.user))
        VerificationCode.objects.create(user=self.user, code=CODE)

        self.test_country = apps.get_model("countries", "Country").objects.create(
            name="Test Country", iso2="TC", iso3="TCY"
        )

    @override_settings(RATELIMIT_ENABLE=False)
    def test_register_success(self):
        data = {
            "email": "new@example.com",
            "password": PASSWORD,
            "fullname": "new user",
            "phone_number": "+5000000002",
        }
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_user = User.objects.get(email="new@example.com")

    @override_settings(RATELIMIT_ENABLE=False)
    def test_register_failure(self):
        data = {
            "email": USER_EMAIL,
            "password": INVALID_PASSWORD,
            "fullname": "new user",
            "phone_number": "+1234567891",
        }
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_validate_email_success(self):
        data = {"email": self.user.email, "code": CODE}

        response = self.client.post(VALIDATE_EMAIL_URL, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_validate_email_failure(self):
        data = {"email": USER_EMAIL, "code": INVALID_CODE}
        response = self.client.post(VALIDATE_EMAIL_URL, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_login_success_with_email(self):
        data = {"email": USER_EMAIL, "password": PASSWORD}
        response = self.client.post(LOGIN_URL, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_login_failure(self):
        data = {"email": USER_EMAIL, "password": INVALID_PASSWORD}
        response = self.client.post(LOGIN_URL, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_refresh_success(self):
        data = {"refresh": self.refresh}
        response = self.client.post(REFRESH_URL, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_refresh_failure(self):
        data = {"refresh": INVALID_TOKEN}
        response = self.client.post(REFRESH_URL, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_logout_success(self):
        self.client.force_authenticate(user=self.user)
        data = {"refresh": self.refresh}
        response = self.client.post(LOGOUT_URL, data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_logout_failure(self):
        self.client.force_authenticate(user=self.user)
        data = {"refresh": INVALID_TOKEN}
        response = self.client.post(LOGOUT_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_forgot_password_success(self):
        data = {"email": USER_EMAIL}
        response = self.client.post(FORGOT_PASSWORD_URL, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_forgot_password_failure(self):
        data = {"email": INVALID_EMAIL}
        response = self.client.post(FORGOT_PASSWORD_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_reset_password_failure(self):
        data = {
            "email": USER_EMAIL,
            "password": PASSWORD,
            "token": INVALID_TOKEN,
        }
        response = self.client.post(RESET_PASSWORD_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_resend_verification_code_success(self):
        User.objects.create(email=INVALID_EMAIL, password=PASSWORD, username="qwrewr")
        data = {"email": USER_EMAIL}
        response = self.client.post(RESEND_VERIFICATION_CODE_URL, data)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_resend_verification_code_failure(self):
        data = {"email": INVALID_EMAIL}
        response = self.client.post(RESEND_VERIFICATION_CODE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_resend_verification_code_phone_success(self):
        """Test resending verification code with phone number"""
        data = {"phone_number": self.user.phone_number}
        response = self.client.post(RESEND_VERIFICATION_CODE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_resend_verification_code_both_fields_failure(self):
        """Test that request fails when both email and phone are provided"""
        data = {"email": USER_EMAIL, "phone_number": self.user.phone_number}
        response = self.client.post(RESEND_VERIFICATION_CODE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_resend_verification_code_no_fields_failure(self):
        """Test that request fails when neither email nor phone is provided"""
        data = {}
        response = self.client.post(RESEND_VERIFICATION_CODE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_resend_verification_code_invalid_phone_failure(self):
        """Test that request fails with invalid phone number"""
        data = {"phone_number": "+9999999999"}
        response = self.client.post(RESEND_VERIFICATION_CODE_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_admin_login_success(self):
        admin_user = User.objects.create(
            email="admin@example.com",
            password=PASSWORD,
            is_email_verified=True,
            is_staff=True,
            username="qwrewr",
            is_superuser=True,
        )
        admin_user.set_password(PASSWORD)
        admin_user.save()
        data = {"email": admin_user.email, "password": PASSWORD}
        login_admins_url = f"{LOGIN_URL}?only_admins=true"
        response = self.client.post(login_admins_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_admin_login_failure(self):
        non_admin_user = User.objects.create(
            email="nonadmin@example.com",
            password=INVALID_PASSWORD,
            is_email_verified=True,
            is_staff=False,
            username="qwrewr",
        )
        non_admin_user.set_password(INVALID_PASSWORD)
        non_admin_user.save()
        data = {"email": non_admin_user.email, "password": INVALID_PASSWORD}
        login_admins_url = f"{LOGIN_URL}?only_admins=true"

        response = self.client.post(login_admins_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
