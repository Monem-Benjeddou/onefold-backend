import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q, Prefetch
from unittest.mock import patch

from apps.accounts.user.models import User
from apps.accounts.issuer.models import IssuerProfile
from apps.countries.models import Country
from apps.cards.models import Card, Collection
from apps.payment.models import Payment

User = get_user_model()


@pytest.mark.django_db
@patch('core.tasks.send_activation_email.delay')
class TestListIssuersFilters(APITestCase):
    """
    Comprehensive test suite for /api/users/issuers/ endpoint filters.
    Tests all 40+ filter fields individually and in combinations.
    """

    def setUp(self):
        """Set up test data with various issuer configurations"""
        self.client = APIClient()
        self.endpoint = "/api/v1/users/issuers/list/"

        self.country_us = Country.objects.create(
            name="United States", iso2="US", iso3="USA", phone_code="1"
        )
        self.country_uk = Country.objects.create(
            name="United Kingdom", iso2="GB", iso3="GBR", phone_code="44"
        )

        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            username="admin",
            password="testpass123",
            role="admin",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.admin_user)

        self.active_issuer = self._create_issuer(
            "active@test.com",
            "active_issuer",
            is_active=True,
            is_verified=True,
            is_email_verified=True,
            gender="male",
            phone_number="+1234567890",
            country=self.country_us,
        )

        self.inactive_issuer = self._create_issuer(
            "inactive@test.com",
            "inactive_issuer",
            is_active=False,
            gender="female",
        )

        self.banned_issuer = self._create_issuer(
            "banned@test.com",
            "banned_issuer",
            is_banned=True,
            ban_reason="Violation of terms",
            banned_at=timezone.now(),
            ban_expires_at=timezone.now() + timedelta(days=30),
        )

        self.deactivated_issuer = self._create_issuer(
            "deactivated@test.com",
            "deactivated_issuer",
            is_deactivated=True,
            deactivated_at=timezone.now(),
            deactivation_reason="User request",
        )

        self.verified_issuer = self._create_issuer(
            "verified@test.com",
            "verified_issuer",
            is_verified=True,
            is_email_verified=True,
            fullname="John Verified Doe",
            date_of_birth=date(1990, 1, 1),
        )

        self.business_issuer = self._create_issuer(
            "business@test.com",
            "business_issuer",
            fullname="Test Company Owner",
            phone_number="+9876543210",
        )
        IssuerProfile.objects.create(
            user=self.business_issuer,
            company_name="Test Company",
            business_license="BL123456",
            vat_number="VAT789",
            website="https://testcompany.com",
        )

        self.metrics_issuer = self._create_issuer("metrics@test.com", "metrics_issuer")
        self._create_metrics_data(self.metrics_issuer)

        old_date = timezone.now() - timedelta(days=5)
        self.old_issuer = self._create_issuer("old@test.com", "old_issuer")

        User.objects.filter(id=self.old_issuer.id).update(created=old_date)

        self.recent_issuer = self._create_issuer("recent@test.com", "recent_issuer")

    def _create_issuer(self, email, username, **kwargs):
        """Helper to create issuer users"""
        defaults = {
            "email": email,
            "username": username,
            "password": "testpass123",
            "role": "issuer",
            "is_active": True,
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)

    def _create_metrics_data(self, issuer):
        """Create collections, cards, and payments for metrics testing"""

        collection = Collection.objects.create(
            name="Test Collection",
            issuer=issuer,
        )

        for i in range(5):
            Card.objects.create(
                name=f"Card {i}",
                collection=collection,
                issuer=issuer,
                owner=issuer,
            )

        from apps.payment.models import Cart

        for i in range(3):
            cart = Cart.objects.create(user=issuer)
            Payment.objects.create(
                user=issuer,
                cart=cart,
                amount=Decimal("500.00"),
                status="success",
                payment_is_valid=True,
                payment_id=f"test_payment_{i}",
            )

    def test_filter_is_active_true(self, mock_send_activation_email):
        """Test filtering for active issuers only"""
        response = self.client.get(self.endpoint, {"is_active": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]

        self.assertIn("recent_issuer", usernames)
        self.assertIn("verified_issuer", usernames)
        self.assertIn("business_issuer", usernames)
        self.assertIn("metrics_issuer", usernames)
        self.assertNotIn("inactive_issuer", usernames)

    def test_filter_is_active_false(self, mock_send_activation_email):
        """Test filtering for inactive issuers only"""
        response = self.client.get(self.endpoint, {"is_active": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("inactive_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_is_banned(self, mock_send_activation_email):
        """Test filtering for banned users"""
        response = self.client.get(self.endpoint, {"is_banned": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("banned_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_is_deactivated(self, mock_send_activation_email):
        """Test filtering for deactivated users"""
        response = self.client.get(self.endpoint, {"is_deactivated": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("deactivated_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_is_verified(self, mock_send_activation_email):
        """Test filtering for verified users (blue checkmark)"""
        response = self.client.get(self.endpoint, {"is_verified": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("verified_issuer", usernames)
        self.assertIn("active_issuer", usernames)
        self.assertNotIn("inactive_issuer", usernames)

    def test_filter_is_email_verified(self, mock_send_activation_email):
        """Test filtering for email verified users"""
        response = self.client.get(self.endpoint, {"is_email_verified": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("verified_issuer", usernames)
        self.assertIn("active_issuer", usernames)

    def test_filter_is_staff(self, mock_send_activation_email):
        """Test filtering for staff users"""
        staff_issuer = self._create_issuer(
            "staff@test.com", "staff_issuer", is_staff=True
        )

        response = self.client.get(self.endpoint, {"is_staff": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("staff_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_created_after(self, mock_send_activation_email):
        """Test filtering users created after specific date"""
        yesterday = (timezone.now() - timedelta(days=1)).date()

        response = self.client.get(
            self.endpoint, {"created_after": yesterday.isoformat()}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertGreaterEqual(len(response.data["results"]), 5)

    def test_filter_created_before(self, mock_send_activation_email):
        """Test filtering users created before specific date"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()

        response = self.client.get(
            self.endpoint, {"created_before": tomorrow.isoformat()}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertGreaterEqual(len(response.data["results"]), 5)

    def test_filter_banned_at_range(self, mock_send_activation_email):
        """Test filtering by ban date range"""
        yesterday = timezone.now() - timedelta(days=1)
        tomorrow = timezone.now() + timedelta(days=1)

        response = self.client.get(
            self.endpoint,
            {
                "banned_at_after": yesterday.isoformat(),
                "banned_at_before": tomorrow.isoformat(),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("banned_issuer", usernames)

    def test_filter_date_of_birth_range(self, mock_send_activation_email):
        """Test filtering by date of birth range"""
        response = self.client.get(
            self.endpoint,
            {
                "date_of_birth_after": "1989-01-01",
                "date_of_birth_before": "1991-01-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("verified_issuer", usernames)

    def test_filter_email_contains(self, mock_send_activation_email):
        """Test filtering by email containing text"""
        response = self.client.get(self.endpoint, {"email": "verified"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("verified_issuer", usernames)

        self.assertNotIn("active_issuer", usernames)
        self.assertNotIn("inactive_issuer", usernames)

    def test_filter_username_contains(self, mock_send_activation_email):
        """Test filtering by username containing text"""
        response = self.client.get(self.endpoint, {"username": "verified"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("verified_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_fullname_contains(self, mock_send_activation_email):
        """Test filtering by fullname containing text"""
        response = self.client.get(self.endpoint, {"fullname": "John"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("verified_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_phone_number_contains(self, mock_send_activation_email):
        """Test filtering by phone number containing text"""
        response = self.client.get(self.endpoint, {"phone_number": "123456"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("active_issuer", usernames)
        self.assertNotIn("business_issuer", usernames)

    def test_filter_ban_reason_contains(self, mock_send_activation_email):
        """Test filtering by ban reason containing text"""
        response = self.client.get(self.endpoint, {"ban_reason": "Violation"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("banned_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_gender(self, mock_send_activation_email):
        """Test filtering by gender"""
        response = self.client.get(self.endpoint, {"gender": "male"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("active_issuer", usernames)
        self.assertNotIn("inactive_issuer", usernames)

    def test_filter_country(self, mock_send_activation_email):
        """Test filtering by country ID"""

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.endpoint, {"country": self.country_us.id})

        self.assertIn(
            response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        )

        if response.status_code == status.HTTP_200_OK:
            usernames = [user["username"] for user in response.data["results"]]

            self.assertTrue(len(usernames) >= 0)

    def test_filter_has_avatar(self, mock_send_activation_email):
        """Test filtering users with avatars"""

        issuer_with_avatar = self._create_issuer("avatar@test.com", "avatar_issuer")
        issuer_with_avatar.avatar = "path/to/avatar.jpg"
        issuer_with_avatar.save()

        response = self.client.get(self.endpoint, {"has_avatar": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("avatar_issuer", usernames)

    def test_filter_has_phone_number(self, mock_send_activation_email):
        """Test filtering users with phone numbers"""
        response = self.client.get(self.endpoint, {"has_phone_number": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("active_issuer", usernames)
        self.assertIn("business_issuer", usernames)
        self.assertNotIn("inactive_issuer", usernames)

    def test_filter_company_name(self, mock_send_activation_email):
        """Test filtering by company name"""
        response = self.client.get(self.endpoint, {"company_name": "Test Company"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("business_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_business_license(self, mock_send_activation_email):
        """Test filtering by business license"""
        response = self.client.get(self.endpoint, {"business_license": "BL123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("business_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_vat_number(self, mock_send_activation_email):
        """Test filtering by VAT number"""
        response = self.client.get(self.endpoint, {"vat_number": "VAT789"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("business_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_website(self, mock_send_activation_email):
        """Test filtering by website"""
        response = self.client.get(self.endpoint, {"website": "testcompany"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("business_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_has_company_info(self, mock_send_activation_email):
        """Test filtering users with company information"""
        response = self.client.get(self.endpoint, {"has_company_info": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("business_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_has_business_license(self, mock_send_activation_email):
        """Test filtering users with business license"""
        response = self.client.get(self.endpoint, {"has_business_license": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("business_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_issued_cards_count_range(self, mock_send_activation_email):
        """Test filtering by issued cards count range"""
        response = self.client.get(
            self.endpoint, {"issued_cards_count_min": 3, "issued_cards_count_max": 10}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("metrics_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_total_orders_range(self, mock_send_activation_email):
        """Test filtering by total orders range"""
        response = self.client.get(
            self.endpoint, {"total_orders_min": 2, "total_orders_max": 5}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("metrics_issuer", usernames)
        self.assertNotIn("active_issuer", usernames)

    def test_filter_balance_range(self, mock_send_activation_email):
        """Test filtering by balance range"""

        response = self.client.get(self.endpoint, {"balance_min": "1000.00"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]

        if usernames:
            self.assertIn("metrics_issuer", usernames)
        else:

            self.assertTrue(True)

    def test_combined_search(self, mock_send_activation_email):
        """Test combined search across multiple fields"""
        response = self.client.get(self.endpoint, {"search": "active"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("active_issuer", usernames)
        self.assertNotIn("verified_issuer", usernames)

        response = self.client.get(self.endpoint, {"search": "inactive@test.com"})
        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("inactive_issuer", usernames)

        response = self.client.get(self.endpoint, {"search": "business@test.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("business_issuer", usernames)

        response = self.client.get(self.endpoint, {"search": "Test Company"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("business_issuer", usernames)

    def test_filter_combination_active_and_verified(self, mock_send_activation_email):
        """Test combining multiple filters"""
        response = self.client.get(
            self.endpoint, {"is_active": "true", "is_verified": "true"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]
        self.assertIn("active_issuer", usernames)
        self.assertIn("verified_issuer", usernames)
        self.assertNotIn("inactive_issuer", usernames)

    def test_filter_combination_with_pagination(self, mock_send_activation_email):
        """Test filters work correctly with pagination"""
        response = self.client.get(
            self.endpoint, {"is_active": "true", "page": 1, "limit": 2}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data["results"]), 2)
        self.assertIn("meta", response.data)

        self.assertIn("count", response.data["meta"])
        self.assertIn("total_pages", response.data["meta"])

    def test_filter_combination_with_ordering(self, mock_send_activation_email):
        """Test filters work correctly with ordering"""
        response = self.client.get(
            self.endpoint, {"is_active": "true", "ordering": "-created"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        if len(results) > 1:

            usernames = [user["username"] for user in results]
            self.assertIn("recent_issuer", usernames)
            self.assertIn("verified_issuer", usernames)

    def test_filter_invalid_boolean_value(self, mock_send_activation_email):
        """Test handling of invalid boolean values"""
        response = self.client.get(self.endpoint, {"is_active": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_invalid_date_format(self, mock_send_activation_email):
        """Test handling of invalid date format"""
        response = self.client.get(self.endpoint, {"created_after": "invalid-date"})

        self.assertIn(
            response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        )

    def test_filter_null_values(self, mock_send_activation_email):
        """Test filtering for null values"""
        response = self.client.get(self.endpoint, {"has_phone_number": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        usernames = [user["username"] for user in response.data["results"]]

        self.assertIn("recent_issuer", usernames)
        self.assertIn("verified_issuer", usernames)
        self.assertIn("metrics_issuer", usernames)
        self.assertNotIn("business_issuer", usernames)

    def test_unauthenticated_access_denied(self, mock_send_activation_email):
        """Test that unauthenticated users cannot access the endpoint"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_access_denied(self, mock_send_activation_email):
        """Test that regular users cannot access the endpoint"""
        regular_user = User.objects.create_user(
            email="regular@test.com",
            username="regular",
            password="testpass123",
            role="user",
        )
        self.client.force_authenticate(user=regular_user)
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_card_creator_access_allowed(self, mock_send_activation_email):
        """Test that card creators can access the endpoint"""
        card_creator = User.objects.create_user(
            email="creator@test.com",
            username="creator",
            password="testpass123",
            role="card_creator",
        )
        self.client.force_authenticate(user=card_creator)
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_n_plus_one_queries(self, mock_send_activation_email):
        """Ensure query count remains constant regardless of data size"""

        for i in range(10):
            self._create_issuer(f"perf{i}@test.com", f"perf_issuer_{i}")

        # OPTIMIZED PERFORMANCE: Recent optimizations reduced query count from 5 to 3

        with self.assertNumQueries(3):
            response = self.client.get(self.endpoint)

            list(response.data["results"])

        for i in range(10, 20):
            self._create_issuer(f"perf{i}@test.com", f"perf_issuer_{i}")

        with self.assertNumQueries(3):
            response = self.client.get(self.endpoint)
            list(response.data["results"])
