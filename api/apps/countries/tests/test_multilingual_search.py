from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils.translation import activate, get_language

from apps.countries.models import Country
from apps.countries.utils import get_country_translation


class MultilingualCountrySearchTestCase(TestCase):
    """Test case for multilingual country search functionality."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all test methods."""

        cls.usa = Country.objects.create(
            name="United States",
            iso2="US",
            iso3="USA",
            phone_code="1",
            capital="Washington D.C.",
            region="Americas",
            subregion="Northern America",
        )

        cls.egypt = Country.objects.create(
            name="Egypt",
            iso2="EG",
            iso3="EGY",
            phone_code="20",
            capital="Cairo",
            region="Africa",
            subregion="Northern Africa",
        )

        cls.saudi_arabia = Country.objects.create(
            name="Saudi Arabia",
            iso2="SA",
            iso3="SAU",
            phone_code="966",
            capital="Riyadh",
            region="Asia",
            subregion="Western Asia",
        )

        cls.germany = Country.objects.create(
            name="Germany",
            iso2="DE",
            iso3="DEU",
            phone_code="49",
            capital="Berlin",
            region="Europe",
            subregion="Western Europe",
        )

        cls.france = Country.objects.create(
            name="France",
            iso2="FR",
            iso3="FRA",
            phone_code="33",
            capital="Paris",
            region="Europe",
            subregion="Western Europe",
        )

    def setUp(self):
        """Set up test client for each test method."""
        self.client = APIClient()
        self.url = reverse("countries:country-list")

        self.original_language = get_language()

    def tearDown(self):
        """Clean up after each test method."""

        activate(self.original_language)

    def test_english_name_search(self):
        """Test searching countries by English name."""

        response = self.client.get(f"{self.url}?name=Egypt")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["meta"]["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Egypt")

        response = self.client.get(f"{self.url}?name=Uni")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["meta"]["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "United States")

        response = self.client.get(f"{self.url}?name=germany")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["meta"]["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Germany")

    @override_settings(LANGUAGE_CODE="ar")
    def test_arabic_name_search(self):
        """Test searching countries by Arabic name."""

        activate("ar")

        egypt_ar = get_country_translation("Egypt", "ar")
        saudi_ar = get_country_translation("Saudi Arabia", "ar")

        response = self.client.get(f"{self.url}?name={egypt_ar}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["meta"]["count"], 1)

        self.assertEqual(response.data["results"][0]["name"], egypt_ar)

        partial_saudi = saudi_ar[:5]
        response = self.client.get(f"{self.url}?name={partial_saudi}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["meta"]["count"] >= 1)

        saudi_in_results = False
        for country in response.data["results"]:
            if country["name"] == saudi_ar:
                saudi_in_results = True
                break
        self.assertTrue(saudi_in_results)

    def test_search_parameter_multilingual(self):
        """Test the search parameter with both English and Arabic names."""

        response = self.client.get(f"{self.url}?search=Germany")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["meta"]["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Germany")

        activate("ar")
        response = self.client.get(f"{self.url}?search=France")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["meta"]["count"] >= 1)

        france_found = False
        for country in response.data["results"]:
            if "iso3" in country and country["iso3"] == "FRA":
                france_found = True
                break

        self.assertTrue(france_found, "France should be found in the search results")

    def test_combined_filters_with_multilingual_search(self):
        """Test combining region filter with multilingual name search."""

        response = self.client.get(f"{self.url}?region=Europe&name=Fra")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["meta"]["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "France")

        activate("ar")
        germany_ar = get_country_translation("Germany", "ar")

        response = self.client.get(f"{self.url}?region=Europe&name={germany_ar}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["meta"]["count"] >= 1)

        germany_in_results = any(
            country["name"] == "Germany" for country in response.data["results"]
        )
        self.assertTrue(germany_in_results)

    def test_pagination_with_multilingual_search(self):
        """Test pagination works correctly with multilingual search."""

        for i in range(10):
            Country.objects.create(
                name=f"Test Country {i}",
                iso2=f"T{i}",
                iso3=f"TST{i}",
                phone_code=f"{i}00",
                capital=f"Test Capital {i}",
                region="Test Region",
                subregion="Test Subregion",
            )

        response = self.client.get(f"{self.url}?limit=5&search=Test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertTrue(response.data["meta"]["next"] is not None)

        response = self.client.get(f"{self.url}?limit=5&page=2&search=Test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertTrue(response.data["meta"]["previous"] is not None)

    def test_no_results_multilingual_search(self):
        """Test search with no matching results."""

        response = self.client.get(f"{self.url}?name=NonExistentCountry")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["meta"]["count"], 0)

        activate("ar")
        response = self.client.get(f"{self.url}?name=بلد غير موجود")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["meta"]["count"], 0)
