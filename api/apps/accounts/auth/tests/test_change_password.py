from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from django.test import override_settings

User = get_user_model()

CHANGE_PASSWORD_URL = reverse("auth-change-password")
PASSWORD = "password123"


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    CELERY_TASK_ALWAYS_EAGER=True,
    BROKER_BACKEND="memory",
    RATELIMIT_ENABLE=False,
)
class ChangePasswordTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            email="user@example.com", is_email_verified=True
        )
        self.user.set_password(PASSWORD)
        self.user.save()
        self.refresh = str(RefreshToken.for_user(self.user))
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        data = {
            "old_password": PASSWORD,
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }
        response = self.client.post(CHANGE_PASSWORD_URL, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password("newpassword123"))

    def test_change_password_invalid_old_password(self):
        data = {
            "old_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }
        response = self.client.post(CHANGE_PASSWORD_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatched_new_passwords(self):
        data = {
            "old_password": PASSWORD,
            "new_password": "newpassword123",
            "confirm_password": "differentpassword",
        }
        response = self.client.post(CHANGE_PASSWORD_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_unauthenticated(self):
        self.client.logout()
        data = {
            "old_password": PASSWORD,
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }
        response = self.client.post(CHANGE_PASSWORD_URL, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
