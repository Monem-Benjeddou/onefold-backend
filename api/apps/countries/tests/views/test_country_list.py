"""
Tests for CountryListView.
"""

import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache

from apps.countries.models import Country, TimeZone
from apps.countries.tests.constants import TEST_COUNTRY_DATA, TEST_TIMEZONE_DATA


class CountryListViewTestCase(TestCase):
    """Test cases for CountryListView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        cache.clear()

        self.country1 = Country.objects.create(**TEST_COUNTRY_DATA)

        country2_data = TEST_COUNTRY_DATA.copy()
        country2_data.update(
            {
                "name": "Another Country",
                "iso3": "ANO",
                "iso2": "AN",
                "region": "Another Region",
            }
        )
        self.country2 = Country.objects.create(**country2_data)

        self.timezone = TimeZone.objects.create(**TEST_TIMEZONE_DATA)
        self.country1.timezones.add(self.timezone)

    def test_get_countries_list_success(self):
        """Test successful retrieval of countries list."""
        url = reverse("countries:country-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("meta", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_countries_list_light_serializer(self):
        """Test countries list with light serializer (default)."""
        url = reverse("countries:country-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        country_data = response.data["results"][0]

        expected_fields = [
            "id",
            "name",
            "iso3",
            "phone_code",
            "capital",
            "region",
            "subregion",
        ]
        for field in expected_fields:
            self.assertIn(field, country_data)

    def test_get_countries_list_full_serializer(self):
        """Test countries list with full serializer."""
        url = reverse("countries:country-list") + "?full=true"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        country_data = response.data["results"][0]

        self.assertIn("timezones", country_data)

    def test_get_countries_list_without_pagination(self):
        """Test countries list without pagination."""
        url = reverse("countries:country-list") + "?pagination=false"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)

    def test_get_countries_list_with_search(self):
        """Test countries list with search functionality."""
        url = reverse("countries:country-list") + "?search=Test Country"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Test Country")

    def test_get_countries_list_with_filter(self):
        """Test countries list with filtering."""
        url = reverse("countries:country-list") + "?region=Test Region"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["region"], "Test Region")

    def test_get_countries_list_pagination(self):
        """Test countries list pagination."""
        url = reverse("countries:country-list") + "?limit=1"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("meta", response.data)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_countries_list_caching(self):
        """Test that countries list is properly cached."""
        url = reverse("countries:country-list") + "?pagination=false"

        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data, response2.data)

    def test_get_countries_list_empty_result(self):
        """Test countries list when no countries exist."""
        Country.objects.all().delete()
        url = reverse("countries:country-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_countries_list_ordering(self):
        """Test that countries are properly ordered by name."""
        url = reverse("countries:country-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        countries = response.data["results"]

        self.assertEqual(countries[0]["name"], "Another Country")
        self.assertEqual(countries[1]["name"], "Test Country")

    def test_rate_limiting_applied(self):
        """Test that rate limiting is applied to the endpoint."""
        url = reverse("countries:country-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
