from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.apps import apps

User = get_user_model()


class RegisterViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/v1/auth/register/"

        self.existing_user = User.objects.create_user(
            email="existing@example.com",
            password="password123",
            fullname="Existing User",
            username="existinguser",
            phone_number="+1111111111",
        )

        self.existing_user.save()

        assert User.objects.filter(email="existing@example.com").exists()

        self.test_country = apps.get_model("countries", "Country").objects.create(
            name="Test Country", iso2="TC", iso3="TCY"
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_register_viewset_lowercase_email(self):
        """Test that the register viewset converts emails to lowercase."""

        User.objects.filter(email__iexact="new_user@example.com").delete()

        data = {
            "email": "NEW_USER@EXAMPLE.COM",
            "password": "password123",
            "fullname": "New User",
            "phone_number": "+2222222222",
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(fullname="New User")
        self.assertEqual(user.email, "new_user@example.com")

    def test_register_viewset_existing_email(self):
        """Test that the register viewset rejects existing emails regardless of case."""

        User.objects.filter(email__iexact="existing@example.com").exclude(
            id=self.existing_user.id
        ).delete()

        self.existing_user.email = "existing@example.com"
        self.existing_user.save()

        self.assertTrue(User.objects.filter(email="existing@example.com").exists())

        data = {
            "email": "EXISTING@EXAMPLE.COM",
            "password": "password123",
            "fullname": "New User",
            "phone_number": "+3333333333",
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {
            "email": "ExIsTiNg@eXaMpLe.CoM",
            "password": "password123",
            "fullname": "New User 2",
            "phone_number": "+4444444444",
        }

        self.assertTrue(User.objects.filter(email="existing@example.com").exists())

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_viewset_with_phone_number(self):
        """Test registration with phone_number field."""
        data = {
            "email": "phone_number_user@example.com",
            "password": "password123",
            "fullname": "Phone Number User",
            "phone_number": "1234567890",
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="phone_number_user@example.com")
        self.assertEqual(user.phone_number, "1234567890")

    def test_register_viewset_ignores_location_and_country(self):
        """Test that location and country fields are ignored during registration."""
        data = {
            "email": "ignored_fields@example.com",
            "password": "password123",
            "fullname": "Fields User",
            "phone_number": "+5555555555",
            "location": "Should be ignored",
            "country": self.test_country.id if hasattr(self, "test_country") else 1,
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="ignored_fields@example.com")

        self.assertIsNone(user.country)
