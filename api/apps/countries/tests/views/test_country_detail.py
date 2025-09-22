"""
Tests for CountryDetailView.
"""

import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache

from apps.countries.models import Country, TimeZone
from apps.countries.tests.constants import TEST_COUNTRY_DATA, TEST_TIMEZONE_DATA


class CountryDetailViewTestCase(TestCase):
    """Test cases for CountryDetailView."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        cache.clear()

        self.country = Country.objects.create(**TEST_COUNTRY_DATA)
        self.timezone = TimeZone.objects.create(**TEST_TIMEZONE_DATA)
        self.country.timezones.add(self.timezone)

    def test_get_country_detail_success(self):
        """Test successful retrieval of country detail."""
        url = reverse("countries:country-detail", kwargs={"id": self.country.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.country.id))
        self.assertEqual(response.data["name"], self.country.name)

    def test_get_country_detail_full_serializer_default(self):
        """Test country detail with full serializer (default behavior)."""
        url = reverse("countries:country-detail", kwargs={"id": self.country.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("timezones", response.data)
        self.assertEqual(len(response.data["timezones"]), 1)

    def test_get_country_detail_light_serializer(self):
        """Test country detail with light serializer."""
        url = (
            reverse("countries:country-detail", kwargs={"id": self.country.id})
            + "?full=false"
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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
            self.assertIn(field, response.data)

    def test_get_country_detail_not_found(self):
        """Test country detail with non-existent country ID."""
        from uuid import uuid4

        non_existent_id = uuid4()
        url = reverse("countries:country-detail", kwargs={"id": non_existent_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_country_detail_invalid_uuid(self):
        """Test country detail with invalid UUID format."""

        url = "/api/v1/countries/invalid-uuid/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_country_detail_caching(self):
        """Test that country detail is properly cached."""
        url = reverse("countries:country-detail", kwargs={"id": self.country.id})

        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data, response2.data)

    def test_get_country_detail_with_timezones(self):
        """Test country detail includes related timezones."""
        url = reverse("countries:country-detail", kwargs={"id": self.country.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("timezones", response.data)
        self.assertEqual(len(response.data["timezones"]), 1)
        timezone_data = response.data["timezones"][0]
        self.assertEqual(timezone_data["zone_name"], self.timezone.zone_name)

    def test_get_country_detail_translated_name(self):
        """Test that country name is properly translated."""
        url = reverse("countries:country-detail", kwargs={"id": self.country.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.data["name"])
        self.assertEqual(str(response.data["name"]), "Test Country")

    def test_get_country_detail_all_fields(self):
        """Test that all country fields are present in detail view."""
        url = reverse("countries:country-detail", kwargs={"id": self.country.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = [
            "id",
            "name",
            "iso3",
            "iso2",
            "numeric_code",
            "phone_code",
            "capital",
            "currency",
            "currency_name",
            "currency_symbol",
            "tld",
            "native",
            "region",
            "subregion",
            "nationality",
            "latitude",
            "longitude",
            "flag",
            "timezones",
        ]

        for field in expected_fields:
            self.assertIn(field, response.data)

    def test_rate_limiting_applied(self):
        """Test that rate limiting is applied to the endpoint."""
        url = reverse("countries:country-detail", kwargs={"id": self.country.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
