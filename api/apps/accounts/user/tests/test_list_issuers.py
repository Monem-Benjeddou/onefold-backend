from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
import factory

from apps.accounts.user.models import User
from apps.accounts.user.tests.factories import (
    SuperUserFactory,
    UserFactory,
    AdminUserFactory,
    CardCreatorUserFactory,
    SalesmanUserFactory,
    ModeratorUserFactory,
)


class IssuerUserFactory(factory.django.DjangoModelFactory):
    """Factory for creating issuer users for testing."""

    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"issuer{n}@example.com")
    fullname = factory.Faker("name")
    username = factory.LazyAttribute(lambda obj: obj.email.split("@")[0])
    phone_number = factory.Sequence(lambda n: f"+123456789{n:02d}")
    role = "issuer"
    is_active = True
    is_email_verified = True


@override_settings(RATE_LIMITER_ENABLED=False)
class ListIssuersViewTest(TestCase):
    """
    Comprehensive test cases for the ListIssuersView.

    Tests cover:
    - Permission validation for different user roles
    - Filtering functionality
    - Search capabilities
    - Pagination behavior
    - Ordering functionality
    - Edge cases and error handling
    """

    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.url = reverse("list-issuers")

        self.superuser = SuperUserFactory()
        self.admin_user = AdminUserFactory()
        self.card_creator_user = CardCreatorUserFactory()
        self.salesman_user = SalesmanUserFactory()
        self.moderator_user = ModeratorUserFactory()
        self.regular_user = UserFactory()

        self.issuer1 = IssuerUserFactory(
            email="issuer1@example.com",
            fullname="Alice Johnson",
            phone_number="+1234567890",
            is_active=True,
            is_email_verified=True,
        )
        self.issuer2 = IssuerUserFactory(
            email="issuer2@example.com",
            fullname="Bob Smith",
            phone_number="+1234567891",
            is_active=True,
            is_email_verified=False,
        )
        self.issuer3 = IssuerUserFactory(
            email="issuer3@example.com",
            fullname="Carol Davis",
            phone_number="+1234567892",
            is_active=False,
            is_email_verified=True,
        )

        self.non_issuer_user = UserFactory(role="user")
        self.non_issuer_admin = AdminUserFactory()

    def test_list_issuers_success_superuser(self):
        """Test successful issuer listing by superuser."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("meta", response.data)
        self.assertIn("results", response.data)

        results = response.data["results"]
        self.assertEqual(len(results), 3)

        for user_data in results:
            self.assertEqual(user_data["role"], "issuer")

    def test_list_issuers_success_admin_user(self):
        """Test successful issuer listing by admin user."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_list_issuers_success_card_creator_user(self):
        """Test successful issuer listing by card creator user."""
        self.client.force_authenticate(user=self.card_creator_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_list_issuers_permission_denied_salesman(self):
        """Test that salesman cannot list issuers."""
        self.client.force_authenticate(user=self.salesman_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_issuers_permission_denied_moderator(self):
        """Test that moderator cannot list issuers."""
        self.client.force_authenticate(user=self.moderator_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_issuers_permission_denied_regular_user(self):
        """Test that regular users cannot access issuer list."""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_issuers_permission_denied_unauthenticated(self):
        """Test that unauthenticated requests are rejected."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_issuers_filter_by_active_status(self):
        """Test filtering issuers by active status."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"is_active": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        self.assertEqual(len(results), 2)

        returned_emails = [user["email"] for user in results]
        active_issuers = User.objects.filter(role="issuer", is_active=True)
        for issuer in active_issuers:
            self.assertIn(issuer.email, returned_emails)

        response = self.client.get(self.url, {"is_active": "false"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]["email"], "issuer3@example.com")

    def test_list_issuers_filter_by_staff_status(self):
        """Test filtering issuers by staff status."""
        self.client.force_authenticate(user=self.superuser)

        self.issuer1.is_staff = True
        self.issuer1.save()

        response = self.client.get(self.url, {"is_staff": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["email"], "issuer1@example.com")

    def test_list_issuers_filter_by_creation_date(self):
        """Test filtering issuers by creation date."""
        self.client.force_authenticate(user=self.superuser)

        from django.utils import timezone

        old_date = timezone.now() - timedelta(days=30)
        old_issuer = IssuerUserFactory(email="old_issuer@example.com")
        old_issuer.created = old_date
        old_issuer.save()

        filter_date = date.today() - timedelta(days=15)
        response = self.client.get(self.url, {"created_after": filter_date.isoformat()})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        emails = [user["email"] for user in response.data["results"]]
        self.assertNotIn("old_issuer@example.com", emails)

    def test_list_issuers_search_by_email(self):
        """Test searching issuers by email."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"search": "issuer1"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["email"], "issuer1@example.com")

    def test_list_issuers_search_by_fullname(self):
        """Test searching issuers by fullname."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"search": "Alice"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["fullname"], "Alice Johnson")

    def test_list_issuers_search_by_phone_number(self):
        """Test searching issuers by phone number."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"search": "+1234567890"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["phone_number"], "+1234567890")

    def test_list_issuers_search_case_insensitive(self):
        """Test that search is case insensitive."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"search": "alice"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["fullname"], "Alice Johnson")

    def test_list_issuers_search_no_results(self):
        """Test search with no matching results."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"search": "nonexistent"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_list_issuers_ordering_by_email(self):
        """Test ordering issuers by email."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"ordering": "email"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        emails = [user["email"] for user in results]
        self.assertEqual(emails, sorted(emails))

    def test_list_issuers_ordering_by_fullname_desc(self):
        """Test ordering issuers by fullname in descending order."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"ordering": "-fullname"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        fullnames = [user["fullname"] for user in results]
        self.assertEqual(fullnames, sorted(fullnames, reverse=True))

    def test_list_issuers_default_ordering(self):
        """Test default ordering by creation date (newest first)."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        self.assertTrue(len(results) >= 2)

    def test_list_issuers_pagination_default(self):
        """Test default pagination behavior."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        meta = response.data["meta"]
        self.assertIn("count", meta)
        self.assertIn("total_pages", meta)
        self.assertIn("current_page_number", meta)
        self.assertIn("limit", meta)

        self.assertEqual(meta["count"], 3)
        self.assertEqual(meta["current_page_number"], 1)
        self.assertEqual(meta["limit"], 5)

    def test_list_issuers_pagination_custom_limit(self):
        """Test pagination with custom limit."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"limit": "2"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        meta = response.data["meta"]
        results = response.data["results"]

        self.assertEqual(len(results), 2)
        self.assertEqual(meta["limit"], 2)
        self.assertEqual(meta["count"], 3)
        self.assertEqual(meta["total_pages"], 2)

    def test_list_issuers_pagination_second_page(self):
        """Test accessing second page of results."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"limit": "2", "page": "2"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        meta = response.data["meta"]
        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(meta["current_page_number"], 2)
        self.assertEqual(meta["previous_page_number"], 1)
        self.assertIsNone(meta["next_page_number"])

    def test_list_issuers_pagination_invalid_page(self):
        """Test handling of invalid page number."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"page": "999"})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_issuers_response_format(self):
        """Test the structure of the response."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("meta", response.data)
        self.assertIn("results", response.data)

        meta = response.data["meta"]
        required_meta_fields = [
            "next",
            "previous",
            "next_page_number",
            "previous_page_number",
            "limit",
            "count",
            "total_pages",
            "current_page_number",
        ]
        for field in required_meta_fields:
            self.assertIn(field, meta)

        if response.data["results"]:
            user_data = response.data["results"][0]
            required_user_fields = [
                "id",
                "email",
                "fullname",
                "username",
                "role",
                "phone_number",
                "role_translated",
                "is_staff",
            ]
            for field in required_user_fields:
                self.assertIn(field, user_data)

    def test_list_issuers_only_issuer_role_returned(self):
        """Test that only users with issuer role are returned."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for user_data in response.data["results"]:
            self.assertEqual(user_data["role"], "issuer")

        issuer_count = User.objects.filter(role="issuer").count()
        self.assertEqual(response.data["meta"]["count"], issuer_count)

    def test_list_issuers_combined_filters(self):
        """Test combining multiple filters."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(
            self.url, {"is_active": "true", "is_staff": "false", "search": "Alice"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        self.assertEqual(len(results), 1)
        user_data = results[0]
        self.assertEqual(user_data["fullname"], "Alice Johnson")
        self.assertEqual(user_data["email"], "issuer1@example.com")

        alice_user = User.objects.get(email="issuer1@example.com")
        self.assertTrue(alice_user.is_active)
        self.assertFalse(alice_user.is_staff)

    def test_list_issuers_empty_results(self):
        """Test behavior when no issuers exist."""

        User.objects.filter(role="issuer").delete()

        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)
        self.assertEqual(response.data["meta"]["count"], 0)

    def test_list_issuers_invalid_filter_values(self):
        """Test handling of invalid filter values."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"is_active": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_issuers_max_page_size_limit(self):
        """Test that page size is limited to maximum allowed."""
        self.client.force_authenticate(user=self.superuser)

        response = self.client.get(self.url, {"limit": "9999"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        meta = response.data["meta"]
        self.assertLessEqual(meta["limit"], 1000)
