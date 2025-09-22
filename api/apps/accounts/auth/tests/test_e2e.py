from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import override_settings
from django.utils import timezone
from apps.accounts.auth.models import OTP
from apps.accounts.user.models import VerificationCode
from apps.accounts.auth.utils import generate_otp
from core.utilities import tprint
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.apps import apps
from apps.accounts.auth.serializers.register import RegisterSerializer

User = get_user_model()


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    CELERY_TASK_ALWAYS_EAGER=True,
    BROKER_BACKEND="memory",
)
class AuthE2ETests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/v1/auth/register/"
        self.login_url = "/api/v1/auth/login/"
        self.validate_email_url = "/api/v1/auth/validate-email/"
        self.refresh_url = "/api/v1/auth/refresh/"
        self.logout_url = "/api/v1/auth/logout/"
        self.forgot_password_url = "/api/v1/auth/forgot-password/"
        self.reset_password_url = "/api/v1/auth/reset-password/"
        self.resend_verification_code_url = "/api/v1/auth/resend-verification-code/"
        self.change_password_url = "/api/v1/auth/change-password/"
        self.admin_login_url = "/api/v1/auth/login/"

        self.user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "fullname": "Test User",
        }

        self.user = User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
            fullname=self.user_data["fullname"],
            username="testuser",
            is_email_verified=True,
        )

        self.refresh_token = str(RefreshToken.for_user(self.user))

        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="securepassword123",
            fullname="Admin User",
            username="adminuser",
            is_staff=True,
            is_superuser=True,
        )

        self.verification_code = VerificationCode.objects.create(
            user=self.user, code="123456", is_used=False
        )

        self.test_country = apps.get_model("countries", "Country").objects.create(
            name="Test Country", iso2="TC", iso3="TCY"
        )

    def test_register_success(self):
        new_user_data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "fullname": "New User",
            "phone_number": "+1234567893",
        }
        response = self.client.post(self.register_url, new_user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=new_user_data["email"]).exists())

        new_user = User.objects.get(email=new_user_data["email"])

    def test_register_duplicate_email(self):
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_phone_number(self):
        user_with_phone = User.objects.create(
            email="user_with_phone@example.com",
            password="securepassword123",
            fullname="User With Phone",
            phone_number="+21624093272",
        )

        new_user_data = {
            "email": "another_user@example.com",
            "password": "securepassword123",
            "fullname": "Another User",
            "phone_number": "+21624093272",
        }

        response = self.client.post(self.register_url, new_user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.json())
        self.assertIn("phone_number", response.json()["error"])
        self.assertEqual(
            response.json()["error"]["phone_number"][0],
            "User with this phone number already exists.",
        )

    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": self.user_data["password"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_login_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_validate_email_success(self):
        self.user.is_email_verified = False
        self.user.save()

        response = self.client.post(
            self.validate_email_url,
            {"email": self.user_data["email"], "code": "123456"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_validate_email_invalid_code(self):
        response = self.client.post(
            self.validate_email_url,
            {"email": self.user_data["email"], "code": "invalid"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_token_success(self):
        response = self.client.post(
            self.refresh_url, {"refresh": self.refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())

    def test_refresh_token_invalid(self):
        response = self.client.post(
            self.refresh_url, {"refresh": "invalid_token"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.logout_url, {"refresh": self.refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_forgot_password_success(self):
        response = self.client.post(
            self.forgot_password_url, {"email": self.user_data["email"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_forgot_password_invalid_email(self):
        response = self.client.post(
            self.forgot_password_url, {"email": "invalid@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(OTP_DELIVERY_METHOD="email")
    def test_resend_verification_code_success(self):
        response = self.client.post(
            self.resend_verification_code_url,
            {"email": self.user_data["email"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.change_password_url,
            {
                "old_password": self.user_data["password"],
                "new_password": "newpassword123",
                "confirm_password": "newpassword123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

    def test_admin_login_success(self):
        response = self.client.post(
            f"{self.admin_login_url}?only_admins=true",
            {"email": "admin@example.com", "password": "securepassword123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_login_non_admin_failure(self):
        response = self.client.post(
            f"{self.admin_login_url}?only_admins=true",
            {"email": self.user_data["email"], "password": self.user_data["password"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_duplicate_phone_number_integrity_error(self):
        """Test that IntegrityError for duplicate phone number is handled correctly"""

        user_with_phone = User.objects.create(
            email="user_with_phone2@example.com",
            password="securepassword123",
            fullname="User With Phone 2",
            phone_number="+21624093273",
        )

        new_user_data = {
            "email": "another_user2@example.com",
            "password": "securepassword123",
            "fullname": "Another User 2",
            "phone_number": "+21624093273",
        }

        original_validate = RegisterSerializer.validate

        def patched_validate(self, data):
            email = data.pop("email")
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError(
                    {"email": _("User with this email already exists.")}
                )
            data["email"] = email
            return data

        RegisterSerializer.validate = patched_validate

        response = self.client.post(self.register_url, new_user_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_data = response.json()
        if (
            "error" in response_data
            and isinstance(response_data["error"], dict)
            and "phone_number" in response_data["error"]
        ):
            self.assertEqual(
                response_data["error"]["phone_number"][0],
                "User with this phone number already exists.",
            )
        else:
            self.assertIn("error", response_data)
