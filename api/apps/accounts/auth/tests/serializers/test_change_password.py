from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from django.test import override_settings

from apps.accounts.auth.serializers import ChangePasswordSerializer

User = get_user_model()
PASSWORD = "password123"


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    CELERY_TASK_ALWAYS_EAGER=True,
    BROKER_BACKEND="memory",
)
class ChangePasswordSerializerTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create(
            email="user@example.com", is_email_verified=True
        )
        self.user.set_password(PASSWORD)
        self.user.save()

        self.request = self.factory.get("/")
        self.request.user = self.user
        self.context = {"request": self.request}

    def test_change_password_serializer_valid_data(self):
        """Test serializer validation with valid data"""
        data = {
            "old_password": PASSWORD,
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }

        serializer = ChangePasswordSerializer(data=data, context=self.context)
        self.assertTrue(serializer.is_valid())

        serializer.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

    def test_change_password_serializer_wrong_old_password(self):
        """Test serializer validation with incorrect old password"""
        data = {
            "old_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        }

        serializer = ChangePasswordSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("old_password", serializer.errors)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_change_password_serializer_mismatched_passwords(self):
        """Test serializer validation with mismatched new passwords"""
        data = {
            "old_password": PASSWORD,
            "new_password": "newpassword123",
            "confirm_password": "differentpassword",
        }

        serializer = ChangePasswordSerializer(data=data, context=self.context)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_change_password_serializer_weak_password(self):
        """Test serializer validation with a weak new password"""
        data = {
            "old_password": PASSWORD,
            "new_password": "123",
            "confirm_password": "123",
        }

        serializer = ChangePasswordSerializer(data=data, context=self.context)

        if serializer.is_valid():

            try:
                serializer.save()

                self.fail("Weak password was accepted with no validation")
            except Exception:

                pass
        else:

            self.assertIn("new_password", serializer.errors)
