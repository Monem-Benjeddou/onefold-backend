from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils.translation import activate, get_language, gettext as _
from django.conf import settings
from typing import Dict, List, Any, Optional

from apps.countries.models import Country, TimeZone
from apps.accounts.user.models import User
from apps.countries import constants


class CountryTranslationTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
            username="testuser",
            is_email_verified=True,
        )

        cls.timezone_ksa = TimeZone.objects.create(
            zone_name="Asia/Riyadh",
            gmt_offset=10800,
            gmt_offset_name="UTC+03:00",
            abbreviation="AST",
            tz_name="Arabia Standard Time",
        )

        cls.timezone_egypt = TimeZone.objects.create(
            zone_name="Africa/Cairo",
            gmt_offset=7200,
            gmt_offset_name="UTC+02:00",
            abbreviation="EET",
            tz_name="Eastern European Time",
        )

        cls.saudi_arabia = Country.objects.create(
            name="Saudi Arabia",
            iso3="SAU",
            iso2="SA",
            phone_code="966",
            capital="Riyadh",
            currency="SAR",
            currency_name="Saudi riyal",
            currency_symbol="﷼",
            region="Asia",
            subregion="Western Asia",
            nationality="Saudi Arabian",
            is_active=True,
        )
        cls.saudi_arabia.timezones.add(cls.timezone_ksa)

        cls.egypt = Country.objects.create(
            name="Egypt",
            iso3="EGY",
            iso2="EG",
            phone_code="20",
            capital="Cairo",
            currency="EGP",
            currency_name="Egyptian pound",
            currency_symbol="£",
            region="Africa",
            subregion="Northern Africa",
            nationality="Egyptian",
            is_active=True,
        )
        cls.egypt.timezones.add(cls.timezone_egypt)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        activate(settings.LANGUAGE_CODE)

    @override_settings(LANGUAGE_CODE="en")
    def test_country_list_english_translation(self):
        """Test that country names are translated to English"""
        activate("en")

        response = self.client.get(
            reverse("countries:country-list"), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertTrue(
            "results" in response_data, "Response should contain 'results' key"
        )

        saudi_arabia = None
        for country in response_data["results"]:
            if country.get("iso3") == "SAU":
                saudi_arabia = country
                break

        self.assertIsNotNone(saudi_arabia, "Saudi Arabia should be in the results")
        if saudi_arabia:
            self.assertEqual(saudi_arabia.get("name"), "Saudi Arabia")

    @override_settings(LANGUAGE_CODE="ar")
    def test_country_list_arabic_translation(self):
        """Test that country names are translated to Arabic"""
        activate("ar")

        response = self.client.get(
            reverse("countries:country-list"), HTTP_ACCEPT_LANGUAGE="ar"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertTrue(
            "results" in response_data, "Response should contain 'results' key"
        )

        saudi_arabia = None
        for country in response_data["results"]:
            if country.get("iso3") == "SAU":
                saudi_arabia = country
                break

        self.assertIsNotNone(saudi_arabia, "Saudi Arabia should be in the results")
        if saudi_arabia:
            self.assertEqual(saudi_arabia.get("name"), "المملكة العربية السعودية")

    def test_country_detail_translation(self):
        """Test that country detail view returns translated names"""
        activate("en")
        response = self.client.get(
            reverse("countries:country-detail", kwargs={"id": self.saudi_arabia.id}),
            HTTP_ACCEPT_LANGUAGE="en",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data.get("name"), "Saudi Arabia")

        activate("ar")
        response = self.client.get(
            reverse("countries:country-detail", kwargs={"id": self.saudi_arabia.id}),
            HTTP_ACCEPT_LANGUAGE="ar",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data.get("name"), "المملكة العربية السعودية")

    def test_country_translation_with_timezones(self):
        """Test that country detail view includes timezone information"""
        activate("en")
        response = self.client.get(
            reverse("countries:country-detail", kwargs={"id": self.saudi_arabia.id}),
            HTTP_ACCEPT_LANGUAGE="en",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIn("timezones", data)
        self.assertEqual(len(data["timezones"]), 1)
        self.assertEqual(data["timezones"][0]["zone_name"], "Asia/Riyadh")

    def test_country_search_translation(self):
        """Test that country search works with translated names"""
        activate("en")
        response = self.client.get(
            reverse("countries:country-list") + "?search=Saudi",
            HTTP_ACCEPT_LANGUAGE="en",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["meta"]["count"], 1)

        activate("ar")
        response = self.client.get(
            reverse("countries:country-list") + "?search=السعودية",
            HTTP_ACCEPT_LANGUAGE="ar",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertGreaterEqual(data["meta"]["count"], 0)

    def test_country_filter_by_region_translation(self):
        """Test that filtering by region works with translations"""
        activate("en")
        response = self.client.get(
            reverse("countries:country-list") + "?region=Asia",
            HTTP_ACCEPT_LANGUAGE="en",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["meta"]["count"], 1)

        saudi_arabia = None
        for country in data["results"]:
            if country.get("iso3") == "SAU":
                saudi_arabia = country
                break

        self.assertIsNotNone(saudi_arabia)
        if saudi_arabia:
            self.assertEqual(saudi_arabia.get("name"), "Saudi Arabia")

    def test_country_currency_information(self):
        """Test that country currency information is properly displayed"""
        response = self.client.get(
            reverse("countries:country-detail", kwargs={"id": self.saudi_arabia.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data.get("currency"), "SAR")
        self.assertEqual(data.get("currency_name"), "Saudi riyal")
        self.assertEqual(data.get("currency_symbol"), "﷼")

    def tearDown(self):
        activate(settings.LANGUAGE_CODE)
