import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.user.models import User
from apps.countries.models import Country, TimeZone
from core.utilities import tprint

CACHE_TTL = 60 * 60 * 24 * 30


class CountryViewsTest(APITestCase):
    def setUp(self):
        self.timezone = TimeZone.objects.create(
            zone_name="America/New_York",
            gmt_offset=-18000,
            gmt_offset_name="UTC-05:00",
            abbreviation="EST",
            tz_name="Eastern Standard Time",
        )

        self.country = Country.objects.create(
            name="Test Country",
            iso3="TST",
            iso2="TS",
            phone_code="123",
            capital="Test Capital",
            region="Test Region",
            subregion="Test Subregion",
            currency="USD",
            currency_name="US Dollar",
            currency_symbol="$",
            nationality="Test",
            is_active=True,
        )
        self.country.timezones.add(self.timezone)

        self.user = User.objects.create_user(
            email="user@user.com", password="password", username="user"
        )
        self.client.force_authenticate(user=self.user)

    def test_country_list_view(self):
        url = reverse("countries:country-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Test Country", response.json()["results"][0]["name"])

    def test_country_detail_view(self):
        url = reverse("countries:country-detail", kwargs={"id": self.country.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], "Test Country")

    def test_country_detail_view_not_found(self):
        url = reverse("countries:country-detail", kwargs={"id": uuid.uuid4()})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_country_has_timezones(self):
        self.assertTrue(self.country.timezones.exists())

    def test_country_list_no_pagination(self):
        url = reverse("countries:country-list") + "?pagination=false"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_country_list_full_details(self):
        url = reverse("countries:country-list") + "?full=true"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("timezones", response.json()["results"][0])

    def test_country_list_with_search(self):
        url = reverse("countries:country-list") + "?search=Test"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Test Country", response.json()["results"][0]["name"])

    def test_country_detail_with_timezones(self):
        url = reverse("countries:country-detail", kwargs={"id": self.country.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["timezones"]), 1)
        self.assertEqual(
            response.json()["timezones"][0]["zone_name"], "America/New_York"
        )

    def test_country_filtering_by_region(self):
        url = reverse("countries:country-list") + "?region=Test Region"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)

    def test_country_filtering_by_currency(self):
        url = reverse("countries:country-list") + "?currency=USD"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)

    def test_country_filtering_by_active_status(self):
        url = reverse("countries:country-list") + "?is_active=true"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["meta"]["count"], 1)
