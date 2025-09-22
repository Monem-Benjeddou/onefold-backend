from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.cache import cache
from unittest.mock import patch, MagicMock
import uuid

from apps.countries.models import Country, TimeZone
from apps.accounts.user.models import User


class CountryViewsTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
            username="testuser",
            is_email_verified=True,
        )

        cls.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
            username="admin",
            is_email_verified=True,
        )

        cls.timezone1 = TimeZone.objects.create(
            zone_name="America/New_York",
            gmt_offset=-18000,
            gmt_offset_name="UTC-05:00",
            abbreviation="EST",
            tz_name="Eastern Standard Time",
        )

        cls.timezone2 = TimeZone.objects.create(
            zone_name="Europe/London",
            gmt_offset=0,
            gmt_offset_name="UTC±00:00",
            abbreviation="GMT",
            tz_name="Greenwich Mean Time",
        )

        cls.country1 = Country.objects.create(
            name="United States",
            iso2="US",
            iso3="USA",
            numeric_code="840",
            phone_code="1",
            capital="Washington",
            currency="USD",
            currency_name="United States dollar",
            currency_symbol="$",
            tld=".us",
            native="United States",
            region="Americas",
            subregion="Northern America",
            nationality="American",
            latitude=37.09024,
            longitude=-95.712891,
            emoji="🇺🇸",
            is_active=True,
        )

        cls.country2 = Country.objects.create(
            name="United Kingdom",
            iso2="GB",
            iso3="GBR",
            numeric_code="826",
            phone_code="44",
            capital="London",
            currency="GBP",
            currency_name="British pound",
            currency_symbol="£",
            tld=".uk",
            native="United Kingdom",
            region="Europe",
            subregion="Northern Europe",
            nationality="British",
            latitude=55.378051,
            longitude=-3.435973,
            emoji="🇬🇧",
            is_active=True,
        )

        cls.country3 = Country.objects.create(
            name="Inactive Country",
            iso2="IC",
            iso3="INC",
            numeric_code="999",
            phone_code="999",
            capital="Inactive Capital",
            region="Test Region",
            subregion="Test Subregion",
            is_active=False,
        )

        cls.country1.timezones.add(cls.timezone1)
        cls.country2.timezones.add(cls.timezone2)

    def setUp(self):
        self.client = APIClient()
        cache.clear()

    def test_country_list_view_authenticated(self):
        """Test that authenticated users can access the country list view"""
        self.client.force_authenticate(user=self.user)
        url = reverse("countries:country-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 3)

    def test_country_list_view_unauthenticated(self):
        """Test that unauthenticated users can access the country list view"""
        url = reverse("countries:country-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 3)

    def test_country_list_view_full_details(self):
        """Test that the full parameter returns detailed country information"""
        self.client.force_authenticate(user=self.user)
        url = reverse("countries:country-list") + "?full=true"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 3)
        self.assertIn("timezones", response.json()["results"][0])
        self.assertIn("timezone_count", response.json()["results"][0])

    def test_country_list_view_no_pagination(self):
        """Test that pagination can be disabled"""
        self.client.force_authenticate(user=self.user)
        url = reverse("countries:country-list") + "?pagination=false"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)
        self.assertGreaterEqual(len(response.json()), 3)

    def test_country_list_view_filtering_by_region(self):
        """Test filtering countries by region"""
        self.client.force_authenticate(user=self.user)
        url = reverse("countries:country-list") + f"?region={self.country1.region}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)

    def test_country_list_view_filtering_by_active_status(self):
        """Test filtering countries by active status"""
        self.client.force_authenticate(user=self.user)
        url = reverse("countries:country-list") + "?is_active=true"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 2)

    def test_country_list_view_filtering_by_currency(self):
        """Test filtering countries by currency"""
        self.client.force_authenticate(user=self.user)
        url = reverse("countries:country-list") + "?currency=USD"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)

    def test_country_list_view_search(self):
        """Test searching countries by name"""
        self.client.force_authenticate(user=self.user)
        url = reverse("countries:country-list") + "?search=United States"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "United States")

    def test_country_list_view_search_by_iso_code(self):
        """Test searching countries by ISO code"""
        self.client.force_authenticate(user=self.user)
        url = reverse("countries:country-list") + "?search=USA"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)

    def test_country_detail_view(self):
        """Test retrieving a specific country"""
        self.client.force_authenticate(user=self.user)
        url = reverse("countries:country-detail", kwargs={"id": self.country1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], "United States")
        self.assertIn("timezones", response.json())
        self.assertIn("timezone_count", response.json())
        self.assertIn("timezone_list", response.json())

    def test_country_detail_view_light(self):
        """Test retrieving a specific country with light details"""
        self.client.force_authenticate(user=self.user)
        url = (
            reverse("countries:country-detail", kwargs={"id": self.country1.id})
            + "?full=false"
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], "United States")

        self.assertNotIn("timezone_count", response.json())

    def test_country_detail_view_not_found(self):
        """Test retrieving a non-existent country"""
        self.client.force_authenticate(user=self.user)
        non_existent_id = uuid.uuid4()
        url = reverse("countries:country-detail", kwargs={"id": non_existent_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_country_timezone_relationships(self):
        """Test that country-timezone relationships work correctly"""
        self.client.force_authenticate(user=self.user)
        url = reverse("countries:country-detail", kwargs={"id": self.country1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["timezone_count"], 1)
        self.assertEqual(len(data["timezone_list"]), 1)
        self.assertIn("America/New_York", data["timezone_list"])

    def test_country_properties(self):
        """Test country model properties"""
        self.client.force_authenticate(user=self.user)
        url = reverse("countries:country-detail", kwargs={"id": self.country1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["flag"], "🇺🇸")
        self.assertTrue(data["is_active"])


class CountryCachingTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
            username="testuser",
            is_email_verified=True,
        )

        cls.timezone1 = TimeZone.objects.create(
            zone_name="America/New_York",
            gmt_offset=-18000,
            gmt_offset_name="UTC-05:00",
            abbreviation="EST",
            tz_name="Eastern Standard Time",
        )

        cls.country1 = Country.objects.create(
            name="Test Country",
            iso2="TC",
            iso3="TCY",
            phone_code="123",
            capital="Test Capital",
            region="Test Region",
            subregion="Test Subregion",
            is_active=True,
        )

        cls.country1.timezones.add(cls.timezone1)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_country_list_caching(self):
        """Test that country list responses are cached properly"""
        url = reverse("countries:country-list") + "?pagination=false"

        with patch("core.decorators.cache_control.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set = MagicMock()
            response1 = self.client.get(url)

            self.assertEqual(response1.status_code, status.HTTP_200_OK)

            mock_cache.get.assert_called()
            mock_cache.set.assert_called()

        with patch("core.decorators.cache_control.cache") as mock_cache:
            mock_cache.get.return_value = response1
            response2 = self.client.get(url)

            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            mock_cache.get.assert_called()

    def test_country_detail_caching(self):
        """Test that country detail responses are cached properly"""
        url = reverse("countries:country-detail", kwargs={"id": self.country1.id})

        with patch("core.decorators.cache_control.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set = MagicMock()
            response1 = self.client.get(url)

            self.assertEqual(response1.status_code, status.HTTP_200_OK)

            mock_cache.get.assert_called()
            mock_cache.set.assert_called()

        with patch("core.decorators.cache_control.cache") as mock_cache:
            mock_cache.get.return_value = response1
            response2 = self.client.get(url)

            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            mock_cache.get.assert_called()

    def test_cache_invalidation(self):
        """Test that cache is properly invalidated when needed"""
        url = reverse("countries:country-list") + "?pagination=false"

        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        cache.clear()

        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)


class CountryFilteringTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
            username="testuser",
            is_email_verified=True,
        )

        cls.timezone1 = TimeZone.objects.create(
            zone_name="America/New_York",
            gmt_offset=-18000,
            gmt_offset_name="UTC-05:00",
            abbreviation="EST",
            tz_name="Eastern Standard Time",
        )

        cls.country_with_timezone = Country.objects.create(
            name="Country With Timezone",
            iso2="CW",
            iso3="CWT",
            region="Americas",
            is_active=True,
        )

        cls.country_without_timezone = Country.objects.create(
            name="Country Without Timezone",
            iso2="CN",
            iso3="CNT",
            region="Europe",
            is_active=True,
        )

        cls.country_with_timezone.timezones.add(cls.timezone1)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_filter_countries_with_timezones(self):
        """Test filtering countries that have timezones"""
        url = reverse("countries:country-list") + "?has_timezones=true"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "Country With Timezone")

    def test_filter_countries_without_timezones(self):
        """Test filtering countries that don't have timezones"""
        url = reverse("countries:country-list") + "?has_timezones=false"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(
            response.json()["results"][0]["name"], "Country Without Timezone"
        )
