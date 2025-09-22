from django.test import TestCase
from apps.accounts.user.models import User, VerificationCode
from apps.countries.models import Country
import pytest
from django.db import IntegrityError


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            username="testuser",
            is_email_verified=True,
        )
        self.country = Country.objects.create(
            name="Test Country",
            iso3="TST",
            iso2="TS",
            phone_code="123",
            capital="Test Capital",
            region="Test Region",
            subregion="Test Subregion",
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.username, "testuser")
        self.assertTrue(self.user.is_email_verified)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_user_with_country(self):
        self.user.country = self.country
        self.user.save()

        self.assertEqual(self.user.country, self.country)
        self.assertEqual(self.user.country.name, "Test Country")
        self.assertEqual(self.user.country.iso3, "TST")


class VerificationCodeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            username="testuser",
            is_email_verified=True,
        )

    def test_verification_code_creation(self):
        code = VerificationCode.objects.create(user=self.user)
        self.assertEqual(len(code.code), 6)
        self.assertFalse(code.is_used)
        self.assertEqual(code.user, self.user)

    def test_verification_code_generation(self):
        code1 = VerificationCode.generate_code()
        code2 = VerificationCode.generate_code()
        self.assertEqual(len(code1), 6)
        self.assertEqual(len(code2), 6)
        self.assertNotEqual(code1, code2)


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            fullname="Test User",
            password="password123",
        )
        assert user.fullname == "Test User"
        assert user.email == "test@example.com"
        assert user.check_password("password123")

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            fullname="Admin User",
            password="admin123",
        )
        assert user.is_superuser
        assert user.is_staff

    def test_unique_email(self):
        User.objects.create_user(
            username="user1",
            email="duplicate@example.com",
            fullname="User One",
            password="password123",
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="user2",
                email="duplicate@example.com",
                fullname="User Two",
                password="password456",
            )

    def test_null_email_allowed(self):
        user = User.objects.create_user(
            username="noemail", fullname="No Email", password="password123", email=""
        )
        assert user.email == ""
