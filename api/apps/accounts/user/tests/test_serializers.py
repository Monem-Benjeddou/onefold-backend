from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from apps.accounts.user.models import User
from apps.accounts.user.serializers import (
    UserSerializer,
    CreateUserSerializer,
    UpdateUserSerializer,
)
from apps.countries.models import Country
from apps.accounts.user.constants import ROLE_CHOICES
from django.contrib.auth import get_user_model
from apps.accounts.issuer.models import IssuerProfile, IssuerProfileImage
from django.core.files.base import ContentFile


User = get_user_model()


class UserSerializerTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "username": "testuser",
            "fullname": "Test User",
            "phone_number": "1234567890",
            "role": "user",
        }
        self.user = User.objects.create_user(**self.user_data)
        self.country = Country.objects.create(
            name="Test Country",
            iso3="TST",
            iso2="TS",
            phone_code="123",
            capital="Test Capital",
            region="Test Region",
            subregion="Test Subregion",
        )

    def test_user_serializer(self):
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data["email"], self.user_data["email"])
        self.assertEqual(data["username"], self.user_data["username"])
        self.assertEqual(data["fullname"], self.user_data["fullname"])
        self.assertEqual(data["phone_number"], self.user_data["phone_number"])
        self.assertEqual(data["role"], self.user_data["role"])
        self.assertIsNone(data["country"])
        self.assertIsNone(data["country_name"])

    def test_role_translated_field(self):
        """Test that role_translated field contains the translated role name"""

        for role_key, role_name in ROLE_CHOICES:
            self.user.role = role_key
            self.user.save()

            serializer = UserSerializer(self.user)
            data = serializer.data

            self.assertEqual(data["role"], role_key)
            self.assertEqual(data["role_translated"], _(role_name))

    def test_user_serializer_with_country(self):
        self.user.country = self.country
        self.user.save()

        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(str(data["country"]), str(self.country.id))
        self.assertEqual(data["country_name"], self.country.name)

    def test_create_user_serializer(self):
        data = {
            "email": "newuser@example.com",
            "fullname": "New User",
            "phone_number": "0987654321",
            "role": "user",
            "country": self.country.id,
        }

        serializer = CreateUserSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.email, data["email"])
        self.assertEqual(user.fullname, data["fullname"])
        self.assertEqual(user.phone_number, data["phone_number"])
        self.assertEqual(user.role, data["role"])
        self.assertEqual(user.country, self.country)

    def test_update_user_serializer(self):
        data = {
            "fullname": "Updated User",
            "phone_number": "5555555555",
            "country": self.country.id,
        }

        serializer = UpdateUserSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.fullname, data["fullname"])
        self.assertEqual(user.phone_number, data["phone_number"])
        self.assertEqual(user.country, self.country)


class UserSerializerIssuerAvatarTest(TestCase):
    def setUp(self):
        self.issuer = User.objects.create_user(
            email="issuer3@test.com",
            username="issuer3",
            role="issuer",
            password="pass12345",
        )

    def test_avatar_from_profile_avatar(self):
        profile = IssuerProfile.objects.create(user=self.issuer)
        profile.avatar.save("test.jpg", ContentFile(b"fake"))
        serializer = UserSerializer(
            instance=self.issuer, context={"request": self._fake_request()}
        )
        data = serializer.data
        self.assertIsNotNone(data.get("avatar"))

    def test_avatar_from_active_profile_image(self):
        IssuerProfile.objects.create(user=self.issuer)
        img = IssuerProfileImage.objects.create(user=self.issuer, is_active=True)
        img.image.save("test2.jpg", ContentFile(b"fake2"))
        serializer = UserSerializer(
            instance=self.issuer, context={"request": self._fake_request()}
        )
        data = serializer.data
        self.assertIsNotNone(data.get("avatar"))

    def _fake_request(self):
        class Dummy:
            def build_absolute_uri(self, path):
                return f"http://testserver{path}"

        return Dummy()
