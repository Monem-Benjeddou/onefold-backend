"""
Simple test to isolate transaction issues.
"""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

User = get_user_model()


@override_settings(
    CACHALOT_ENABLED=False,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class SimpleAuthTest(TestCase):
    """Simple test without cachalot interference."""

    def test_create_user(self):
        """Test basic user creation."""
        user = User.objects.create(email="simple@example.com", is_email_verified=True)
        user.set_password("password123")
        user.save()

        self.assertEqual(user.email, "simple@example.com")
        self.assertTrue(user.check_password("password123"))
