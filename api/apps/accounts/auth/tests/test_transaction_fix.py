"""
Simple test to verify the transaction fix works correctly.
Uses Django's standard TestCase without the complex isolation system.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.accounts.auth.models import OTP
from apps.accounts.auth.utils import generate_otp

User = get_user_model()


class TransactionFixTest(TestCase):
    """Test the AbstractAutoIncrementModel transaction fix."""

    def test_user_creation_basic(self):
        """Test that User creation works without transaction conflicts."""
        user = User.objects.create_user(
            email="test_basic@example.com",
            username="test_basic_user",
            fullname="Test Basic User",
        )

        self.assertIsNotNone(user.id)
        self.assertIsNotNone(user._id)
        self.assertEqual(user.email, "test_basic@example.com")

    def test_user_creation_with_atomic_transaction(self):
        """Test that User creation works within atomic transactions."""
        with transaction.atomic():
            user = User.objects.create_user(
                email="test_atomic@example.com",
                username="test_atomic_user",
                fullname="Test Atomic User",
            )

        self.assertIsNotNone(user.id)
        self.assertIsNotNone(user._id)
        self.assertEqual(user.email, "test_atomic@example.com")

    def test_otp_generation_basic(self):
        """Test that OTP generation works without transaction conflicts."""
        user = User.objects.create_user(
            email="test_otp@example.com",
            username="test_otp_user",
            fullname="Test OTP User",
        )

        code = user.generate_verification_code()

        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

        otp = OTP.objects.get(user=user, code=code)
        self.assertEqual(otp.code, code)
        self.assertTrue(otp.is_valid())

    def test_otp_generation_in_atomic_transaction(self):
        """Test that OTP generation works within atomic transactions."""
        user = User.objects.create_user(
            email="test_otp_atomic@example.com",
            username="test_otp_atomic_user",
            fullname="Test OTP Atomic User",
        )

        with transaction.atomic():
            code = user.generate_verification_code()

        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

        otp = OTP.objects.get(user=user, code=code)
        self.assertEqual(otp.code, code)
        self.assertTrue(otp.is_valid())

    def test_multiple_user_creation(self):
        """Test multiple user creation to verify _id uniqueness."""
        users = []

        for i in range(5):
            user = User.objects.create_user(
                email=f"test_multi_{i}@example.com",
                username=f"test_multi_user_{i}",
                fullname=f"Test Multi User {i}",
            )
            users.append(user)

        user_ids = [u._id for u in users]
        self.assertEqual(
            len(user_ids), len(set(user_ids)), "All _id values should be unique"
        )

        for user_id in user_ids:
            self.assertIsInstance(user_id, int)
            self.assertGreater(user_id, 0)
