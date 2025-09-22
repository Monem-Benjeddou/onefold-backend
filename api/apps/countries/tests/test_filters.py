from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import uuid
from unittest import mock
from django.utils.translation import activate, get_language

from apps.accounts.user.models import User
from apps.countries.models import Country, TimeZone
from apps.countries.filters import CountryFilterSet


class CountryFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
            username="testuser",
            is_email_verified=True,
        )
        self.client.force_authenticate(user=self.user)

        self.timezone_est = TimeZone.objects.create(
            zone_name="America/New_York",
            gmt_offset=-18000,
            gmt_offset_name="UTC-05:00",
            abbreviation="EST",
            tz_name="Eastern Standard Time",
        )

        self.timezone_gmt = TimeZone.objects.create(
            zone_name="Europe/London",
            gmt_offset=0,
            gmt_offset_name="UTC±00:00",
            abbreviation="GMT",
            tz_name="Greenwich Mean Time",
        )

        self.usa = Country.objects.create(
            name="United States",
            iso3="USA",
            iso2="US",
            phone_code="1",
            capital="Washington",
            currency="USD",
            currency_name="United States dollar",
            currency_symbol="$",
            region="Americas",
            subregion="Northern America",
            nationality="American",
            is_active=True,
        )

        self.canada = Country.objects.create(
            name="Canada",
            iso3="CAN",
            iso2="CA",
            phone_code="1",
            capital="Ottawa",
            currency="CAD",
            currency_name="Canadian dollar",
            currency_symbol="$",
            region="Americas",
            subregion="Northern America",
            nationality="Canadian",
            is_active=True,
        )

        self.france = Country.objects.create(
            name="France",
            iso3="FRA",
            iso2="FR",
            phone_code="33",
            capital="Paris",
            currency="EUR",
            currency_name="Euro",
            currency_symbol="€",
            region="Europe",
            subregion="Western Europe",
            nationality="French",
            is_active=True,
        )

        self.japan = Country.objects.create(
            name="Japan",
            iso3="JPN",
            iso2="JP",
            phone_code="81",
            capital="Tokyo",
            currency="JPY",
            currency_name="Japanese yen",
            currency_symbol="¥",
            region="Asia",
            subregion="Eastern Asia",
            nationality="Japanese",
            is_active=True,
        )

        self.inactive_country = Country.objects.create(
            name="Inactive Country",
            iso3="INC",
            iso2="IC",
            phone_code="999",
            capital="Inactive Capital",
            region="Test Region",
            subregion="Test Subregion",
            is_active=False,
        )

        self.usa.timezones.add(self.timezone_est)
        self.france.timezones.add(self.timezone_gmt)

    def test_name_filter(self):
        """Test filtering countries by name"""
        url = reverse("countries:country-list")
        response = self.client.get(f"{url}?name=united")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "United States")

        response = self.client.get(f"{url}?name=an")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.json()["meta"]["count"], 2)

        response = self.client.get(f"{url}?name=xyz")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 0)

    def test_iso_filters(self):
        """Test filtering countries by ISO codes"""
        url = reverse("countries:country-list")
        response = self.client.get(f"{url}?iso3=USA")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "United States")

        response = self.client.get(f"{url}?iso2=JP")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "Japan")

    def test_region_filter(self):
        """Test filtering countries by region"""
        url = reverse("countries:country-list")
        response = self.client.get(f"{url}?region=Americas")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 2)

        response = self.client.get(f"{url}?region=Europe")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "France")

    def test_subregion_filter(self):
        """Test filtering countries by subregion"""
        url = reverse("countries:country-list")
        response = self.client.get(f"{url}?subregion=Northern America")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 2)

        response = self.client.get(f"{url}?subregion=Western Europe")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "France")

    def test_currency_filter(self):
        """Test filtering countries by currency"""
        url = reverse("countries:country-list")
        response = self.client.get(f"{url}?currency=USD")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "United States")

        response = self.client.get(f"{url}?currency=EUR")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "France")

    def test_nationality_filter(self):
        """Test filtering countries by nationality"""
        url = reverse("countries:country-list")
        response = self.client.get(f"{url}?nationality=American")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "United States")

    def test_is_active_filter(self):
        """Test filtering countries by active status"""
        url = reverse("countries:country-list")
        response = self.client.get(f"{url}?is_active=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 4)

        response = self.client.get(f"{url}?is_active=false")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "Inactive Country")

    def test_has_timezones_filter(self):
        """Test filtering countries by timezone presence"""
        url = reverse("countries:country-list")
        response = self.client.get(f"{url}?has_timezones=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 2)

        response = self.client.get(f"{url}?has_timezones=false")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 3)

    def test_search_filter(self):
        """Test searching countries across multiple fields"""
        url = reverse("countries:country-list")
        response = self.client.get(f"{url}?search=united")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "United States")

        response = self.client.get(f"{url}?search=tokyo")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "Japan")

        response = self.client.get(f"{url}?search=America")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.json()["meta"]["count"], 1)

        response = self.client.get(f"{url}?search=USA")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)

        response = self.client.get(f"{url}?search=EUR")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)

    def test_combined_filters(self):
        """Test combining multiple filters"""
        url = reverse("countries:country-list")
        response = self.client.get(f"{url}?region=Americas&is_active=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 2)

        response = self.client.get(f"{url}?region=Europe&currency=EUR")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "France")

        response = self.client.get(f"{url}?has_timezones=true&region=Americas")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "United States")


class CountryFilterSetTestCase(TestCase):
    """Test the CountryFilterSet class directly"""

    def setUp(self):
        self.usa = Country.objects.create(
            name="United States",
            iso3="USA",
            iso2="US",
            is_active=True,
        )

    def tearDown(self):
        activate("en")

    def test_filter_name_english(self):
        """Test filtering by English name"""
        filterset = CountryFilterSet()
        queryset = Country.objects.all()

        filtered_queryset = filterset.filter_name(queryset, "name", "United")
        self.assertEqual(filtered_queryset.count(), 1)
        self.assertEqual(filtered_queryset.first().name, "United States")

        filtered_queryset = filterset.filter_name(queryset, "name", "xyz")
        self.assertEqual(filtered_queryset.count(), 0)

    def test_filter_name_empty_value(self):
        """Test filtering with empty name value"""
        filterset = CountryFilterSet()
        queryset = Country.objects.all()

        filtered_queryset = filterset.filter_name(queryset, "name", "")
        self.assertEqual(filtered_queryset.count(), queryset.count())

        filtered_queryset = filterset.filter_name(queryset, "name", None)
        self.assertEqual(filtered_queryset.count(), queryset.count())

    @mock.patch("apps.countries.filters.get_country_translation")
    def test_filter_name_arabic(self, mock_get_translation):
        """Test filtering by Arabic name"""
        mock_get_translation.return_value = "الولايات المتحدة"

        filterset = CountryFilterSet()
        queryset = Country.objects.all()

        filtered_queryset = filterset.filter_name(queryset, "name", "الولايات")
        self.assertEqual(filtered_queryset.count(), 1)
        self.assertEqual(filtered_queryset.first().name, "United States")

        filtered_queryset = filterset.filter_name(queryset, "name", "United")
        self.assertEqual(filtered_queryset.count(), 1)

        mock_get_translation.return_value = "some other translation"
        filtered_queryset = filterset.filter_name(queryset, "name", "United")
        self.assertEqual(filtered_queryset.count(), 1)

    @mock.patch("apps.countries.filters.get_country_translation")
    def test_filter_search(self, mock_get_translation):
        """Test the search filter method"""
        mock_get_translation.return_value = "الولايات المتحدة"

        filterset = CountryFilterSet()
        queryset = Country.objects.all()

        filtered_queryset = filterset.filter_search(queryset, "search", "United")
        self.assertEqual(filtered_queryset.count(), 1)

        filtered_queryset = filterset.filter_search(queryset, "search", "USA")
        self.assertEqual(filtered_queryset.count(), 1)

        filtered_queryset = filterset.filter_search(queryset, "search", "")
        self.assertEqual(filtered_queryset.count(), queryset.count())

    def test_filter_has_timezones(self):
        """Test filtering by timezone presence"""
        timezone = TimeZone.objects.create(
            zone_name="America/New_York",
            gmt_offset=-18000,
        )

        country_with_tz = Country.objects.create(
            name="Country With TZ",
            iso3="CWT",
            is_active=True,
        )
        country_with_tz.timezones.add(timezone)

        country_without_tz = Country.objects.create(
            name="Country Without TZ",
            iso3="CNT",
            is_active=True,
        )

        filterset = CountryFilterSet()
        queryset = Country.objects.all()

        filtered_queryset = filterset.filter_has_timezones(
            queryset, "has_timezones", True
        )
        self.assertEqual(filtered_queryset.count(), 1)
        self.assertEqual(filtered_queryset.first().name, "Country With TZ")

        filtered_queryset = filterset.filter_has_timezones(
            queryset, "has_timezones", False
        )
        self.assertEqual(filtered_queryset.count(), 2)

        filtered_queryset = filterset.filter_has_timezones(
            queryset, "has_timezones", None
        )
        self.assertEqual(filtered_queryset.count(), queryset.count())
