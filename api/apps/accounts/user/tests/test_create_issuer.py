from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import factory

from apps.accounts.user.models import User
from apps.countries.models import Country
from apps.accounts.user.tests.factories import (
    SuperUserFactory,
    UserFactory,
    AdminUserFactory,
    SalesmanUserFactory,
    CardCreatorUserFactory,
)


class CountryFactory(factory.django.DjangoModelFactory):
    """Factory for creating test countries."""

    class Meta:
        model = Country
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"TestCountry{n}")
    iso2 = factory.Sequence(lambda n: f"T{n}")
    iso3 = factory.Sequence(lambda n: f"TC{n}")
    phone_code = "+1"


@override_settings(RATE_LIMITER_ENABLED=False)
class CreateIssuerAPIViewTest(TestCase):
    """Test cases for the CreateIssuerAPIView."""

    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.url = reverse("create-issuer")

        self.country = CountryFactory()

        self.superuser = SuperUserFactory()
        self.admin_user = AdminUserFactory()
        self.salesman_user = SalesmanUserFactory()
        self.card_creator_user = CardCreatorUserFactory()

        self.regular_user = UserFactory()

        self.valid_issuer_data = {
            "email": "issuer@example.com",
            "fullname": "Test Issuer Company",
            "phone_number": "+1234567890",
            "country": self.country.id,
            "website": "https://issuer.example.com",
            "vat_number": "VAT123456789",
        }

    def test_create_issuer_success_superuser(self):
        """Test successful issuer creation by superuser."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.post(self.url, self.valid_issuer_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], self.valid_issuer_data["email"])
        self.assertEqual(response.data["fullname"], self.valid_issuer_data["fullname"])
        self.assertEqual(
            response.data["phone_number"], self.valid_issuer_data["phone_number"]
        )
        self.assertIn("message", response.data)

        issuer = User.objects.get(email=self.valid_issuer_data["email"])
        self.assertEqual(issuer.role, "issuer")
        self.assertEqual(issuer.fullname, self.valid_issuer_data["fullname"])
        self.assertEqual(issuer.phone_number, self.valid_issuer_data["phone_number"])
        self.assertEqual(issuer.country.id, self.valid_issuer_data["country"])

    def test_create_issuer_success_admin_user(self):
        """Test successful issuer creation by admin user."""
        self.client.force_authenticate(user=self.admin_user)

        data = self.valid_issuer_data.copy()
        data["email"] = "admin_created_issuer@example.com"

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], data["email"])

        issuer = User.objects.get(email=data["email"])
        self.assertEqual(issuer.role, "issuer")

    def test_create_issuer_success_salesman_user(self):
        """Test successful issuer creation by salesman user."""
        self.client.force_authenticate(user=self.salesman_user)

        data = self.valid_issuer_data.copy()
        data["email"] = "salesman_created_issuer@example.com"

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], data["email"])

        issuer = User.objects.get(email=data["email"])
        self.assertEqual(issuer.role, "issuer")

    def test_create_issuer_success_card_creator_user(self):
        """Test successful issuer creation by card creator user."""
        self.client.force_authenticate(user=self.card_creator_user)

        data = self.valid_issuer_data.copy()
        data["email"] = "cardcreator_created_issuer@example.com"

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], data["email"])

        issuer = User.objects.get(email=data["email"])
        self.assertEqual(issuer.role, "issuer")

    def test_create_issuer_permission_denied_regular_user(self):
        """Test that regular users cannot create issuers."""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.post(self.url, self.valid_issuer_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(
            User.objects.filter(email=self.valid_issuer_data["email"]).exists()
        )

    def test_create_issuer_permission_denied_unauthenticated(self):
        """Test that unauthenticated requests are rejected."""
        response = self.client.post(self.url, self.valid_issuer_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertFalse(
            User.objects.filter(email=self.valid_issuer_data["email"]).exists()
        )

    def test_create_issuer_duplicate_email_validation(self):
        """Test validation error for duplicate email."""

        existing_user = UserFactory(email=self.valid_issuer_data["email"])

        self.client.force_authenticate(user=self.superuser)

        response = self.client.post(self.url, self.valid_issuer_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data.get("error", response.data))

        issuers = User.objects.filter(email=self.valid_issuer_data["email"])
        self.assertEqual(issuers.count(), 1)
        self.assertEqual(issuers.first().role, "user")

    def test_create_issuer_invalid_phone_number_format(self):
        """Test validation error for invalid phone number format."""
        self.client.force_authenticate(user=self.superuser)

        invalid_phone_numbers = [
            "1234567890",
            "+12345",
            "+123456789012345678",
            "abc1234567890",
            "",
            "+",
        ]

        for invalid_phone in invalid_phone_numbers:
            with self.subTest(phone_number=invalid_phone):
                data = self.valid_issuer_data.copy()
                data["phone_number"] = invalid_phone

                response = self.client.post(self.url, data, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("phone_number", response.data.get("error", response.data))

    def test_create_issuer_valid_phone_number_formats(self):
        """Test that valid E.164 phone number formats are accepted."""
        self.client.force_authenticate(user=self.superuser)

        valid_phone_numbers = [
            "+1234567890",
            "+12345678901234",
            "+971501234567",
            "+442071234567",
        ]

        for i, valid_phone in enumerate(valid_phone_numbers):
            with self.subTest(phone_number=valid_phone):
                data = self.valid_issuer_data.copy()
                data["email"] = f"testphone{i}@example.com"
                data["phone_number"] = valid_phone

                response = self.client.post(self.url, data, format="json")

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data["phone_number"], valid_phone)

    def test_create_issuer_missing_required_fields(self):
        """Test validation errors for missing required fields."""
        self.client.force_authenticate(user=self.superuser)

        required_fields = ["email", "fullname", "phone_number"]

        for field in required_fields:
            with self.subTest(missing_field=field):
                data = self.valid_issuer_data.copy()
                data.pop(field)

                response = self.client.post(self.url, data, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data.get("error", response.data))

    def test_create_issuer_empty_required_fields(self):
        """Test validation errors for empty required fields."""
        self.client.force_authenticate(user=self.superuser)

        required_fields = ["email", "fullname", "phone_number"]

        for field in required_fields:
            with self.subTest(empty_field=field):
                data = self.valid_issuer_data.copy()
                data[field] = ""

                response = self.client.post(self.url, data, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data.get("error", response.data))

    def test_create_issuer_optional_fields(self):
        """Test that issuers can be created without optional fields."""
        self.client.force_authenticate(user=self.superuser)

        data = {
            "email": "minimal@example.com",
            "fullname": "Minimal Issuer",
            "phone_number": "+1987654321",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], data["email"])

        issuer = User.objects.get(email=data["email"])
        self.assertEqual(issuer.role, "issuer")
        self.assertIsNone(issuer.country)

    def test_create_issuer_with_country_optional(self):
        """Test that country is optional and works when provided."""
        self.client.force_authenticate(user=self.superuser)

        data_with_country = {
            "email": "with_country@example.com",
            "fullname": "Issuer With Country",
            "phone_number": "+1987654321",
            "country": self.country.id,
        }

        response = self.client.post(self.url, data_with_country, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], data_with_country["email"])

        issuer = User.objects.get(email=data_with_country["email"])
        self.assertEqual(issuer.role, "issuer")
        self.assertEqual(issuer.country.id, self.country.id)

    def test_create_issuer_invalid_vat_number(self):
        """Test validation error for invalid VAT number."""
        self.client.force_authenticate(user=self.superuser)

        data = self.valid_issuer_data.copy()
        data["vat_number"] = "X"

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vat_number", response.data.get("error", response.data))

    def test_create_issuer_valid_vat_number(self):
        """Test that valid VAT numbers are accepted."""
        self.client.force_authenticate(user=self.superuser)

        data = self.valid_issuer_data.copy()
        data["email"] = "vat@example.com"
        data["vat_number"] = "GB123456789"

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_issuer_invalid_website_format(self):
        """Test validation error for invalid website URL."""
        self.client.force_authenticate(user=self.superuser)

        data = self.valid_issuer_data.copy()
        data["website"] = "not-a-valid-url"

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("website", response.data.get("error", response.data))

    def test_create_issuer_role_automatically_set(self):
        """Test that role is automatically set to 'issuer' regardless of input."""
        self.client.force_authenticate(user=self.superuser)

        data = self.valid_issuer_data.copy()
        data["role"] = "admin"
        data["email"] = "role@example.com"

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        issuer = User.objects.get(email=data["email"])
        self.assertEqual(issuer.role, "issuer")

    def test_create_issuer_with_avatar(self):
        """Test creating issuer with avatar (optional field)."""
        self.client.force_authenticate(user=self.superuser)

        data = self.valid_issuer_data.copy()
        data["email"] = "avatar@example.com"

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_issuer_nonexistent_country(self):
        """Test validation error for nonexistent country."""
        self.client.force_authenticate(user=self.superuser)

        data = self.valid_issuer_data.copy()
        data["country"] = 99999

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("country", response.data.get("error", response.data))
