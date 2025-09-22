import json
import os
from io import StringIO
from unittest.mock import patch, mock_open
from decimal import Decimal

from django.test import TestCase
from django.core.management import call_command

from apps.countries.models import Country, TimeZone


class SeedCountriesCommandTest(TestCase):
    """Tests for the seed-countries command."""

    def setUp(self):
        self.sample_data = [
            {
                "name": "United States",
                "iso2": "US",
                "iso3": "USA",
                "numeric_code": "840",
                "phone_code": "1",
                "capital": "Washington",
                "currency": "USD",
                "currency_name": "United States dollar",
                "currency_symbol": "$",
                "tld": ".us",
                "native": "United States",
                "region": "Americas",
                "subregion": "Northern America",
                "nationality": "American",
                "latitude": 37.09024,
                "longitude": -95.712891,
                "emoji": "🇺🇸",
                "timezones": [
                    {
                        "zoneName": "America/New_York",
                        "gmtOffset": -18000,
                        "gmtOffsetName": "UTC-05:00",
                        "abbreviation": "EST",
                        "tzName": "Eastern Standard Time",
                    },
                    {
                        "zoneName": "America/Chicago",
                        "gmtOffset": -21600,
                        "gmtOffsetName": "UTC-06:00",
                        "abbreviation": "CST",
                        "tzName": "Central Standard Time",
                    },
                ],
            }
        ]

        self.multi_country_data = [
            self.sample_data[0],
            {
                "name": "United Kingdom",
                "iso2": "GB",
                "iso3": "GBR",
                "numeric_code": "826",
                "phone_code": "44",
                "capital": "London",
                "currency": "GBP",
                "currency_name": "British pound",
                "currency_symbol": "£",
                "tld": ".uk",
                "native": "United Kingdom",
                "region": "Europe",
                "subregion": "Northern Europe",
                "nationality": "British",
                "latitude": 55.378051,
                "longitude": -3.435973,
                "emoji": "🇬🇧",
                "timezones": [
                    {
                        "zoneName": "Europe/London",
                        "gmtOffset": 0,
                        "gmtOffsetName": "UTC±00:00",
                        "abbreviation": "GMT",
                        "tzName": "Greenwich Mean Time",
                    }
                ],
            },
        ]

    def test_command_output_success(self):
        """Test command output when successfully loading data."""
        with patch("builtins.open", mock_open(read_data=json.dumps(self.sample_data))):
            out = StringIO()
            call_command("seed-countries", stdout=out)
            output = out.getvalue()

            self.assertIn("Successfully seeded", output)

            self.assertEqual(Country.objects.count(), 1)
            self.assertEqual(TimeZone.objects.count(), 2)

            country = Country.objects.get(iso3="USA")
            self.assertEqual(country.timezones.count(), 2)

            self.assertEqual(country.name, "United States")
            self.assertEqual(country.currency, "USD")
            self.assertEqual(country.capital, "Washington")
            self.assertTrue(country.is_active)

    def test_skip_if_countries_exist(self):
        """Test that command skips seeding if countries already exist."""
        Country.objects.create(name="Test Country", iso2="TC", iso3="TCO")

        with patch("builtins.open", mock_open(read_data=json.dumps(self.sample_data))):
            out = StringIO()
            call_command("seed-countries", stdout=out)
            output = out.getvalue()

            self.assertIn("Countries already exist. Use --force to re-seed", output)

            self.assertEqual(Country.objects.count(), 1)
            country = Country.objects.first()
            if country:
                self.assertEqual(country.name, "Test Country")

    def test_force_option(self):
        """Test that --force option clears existing data and re-seeds."""
        Country.objects.create(name="Test Country", iso2="TC", iso3="TCO")
        TimeZone.objects.create(zone_name="Test/Timezone")

        with patch("builtins.open", mock_open(read_data=json.dumps(self.sample_data))):
            out = StringIO()
            call_command("seed-countries", "--force", stdout=out)
            output = out.getvalue()

            self.assertIn("Force mode: Clearing existing data", output)
            self.assertIn("Successfully seeded", output)

            self.assertEqual(Country.objects.count(), 1)
            country = Country.objects.first()
            self.assertEqual(country.name, "United States")

    def test_file_not_found_error(self):
        """Test handling of FileNotFoundError."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            out = StringIO()
            err = StringIO()
            call_command("seed-countries", stdout=out, stderr=err)
            error_output = err.getvalue()

            self.assertIn("File not found", error_output)

            self.assertEqual(Country.objects.count(), 0)
            self.assertEqual(TimeZone.objects.count(), 0)

    def test_json_decode_error(self):
        """Test handling of JSONDecodeError."""
        with patch("builtins.open", mock_open(read_data="invalid json data")):
            out = StringIO()
            err = StringIO()
            call_command("seed-countries", stdout=out, stderr=err)
            error_output = err.getvalue()

            self.assertIn("Failed to decode JSON", error_output)

            self.assertEqual(Country.objects.count(), 0)
            self.assertEqual(TimeZone.objects.count(), 0)

    def test_complete_model_creation(self):
        """Test that all models and their relationships are correctly created."""
        with patch("builtins.open", mock_open(read_data=json.dumps(self.sample_data))):
            call_command("seed-countries")

            country = Country.objects.get(iso3="USA")

            self.assertEqual(country.name, "United States")
            self.assertEqual(country.iso2, "US")
            self.assertEqual(country.iso3, "USA")
            self.assertEqual(country.numeric_code, "840")
            self.assertEqual(country.phone_code, "1")
            self.assertEqual(country.capital, "Washington")
            self.assertEqual(country.currency, "USD")
            self.assertEqual(country.currency_name, "United States dollar")
            self.assertEqual(country.currency_symbol, "$")
            self.assertEqual(country.tld, ".us")
            self.assertEqual(country.native, "United States")
            self.assertEqual(country.region, "Americas")
            self.assertEqual(country.subregion, "Northern America")
            self.assertEqual(country.nationality, "American")
            self.assertEqual(float(country.latitude), 37.09024)
            self.assertEqual(float(country.longitude), -95.712891)
            self.assertEqual(country.emoji, "🇺🇸")
            self.assertTrue(country.is_active)

            self.assertEqual(country.timezones.count(), 2)
            timezone_names = list(country.timezones.values_list("zone_name", flat=True))
            self.assertIn("America/New_York", timezone_names)
            self.assertIn("America/Chicago", timezone_names)

    def test_timezone_creation(self):
        """Test that timezones are created correctly."""
        with patch("builtins.open", mock_open(read_data=json.dumps(self.sample_data))):
            call_command("seed-countries")

            self.assertEqual(TimeZone.objects.count(), 2)

            est_timezone = TimeZone.objects.get(zone_name="America/New_York")
            self.assertEqual(est_timezone.gmt_offset, -18000)
            self.assertEqual(est_timezone.gmt_offset_name, "UTC-05:00")
            self.assertEqual(est_timezone.abbreviation, "EST")
            self.assertEqual(est_timezone.tz_name, "Eastern Standard Time")

            cst_timezone = TimeZone.objects.get(zone_name="America/Chicago")
            self.assertEqual(cst_timezone.gmt_offset, -21600)
            self.assertEqual(cst_timezone.gmt_offset_name, "UTC-06:00")
            self.assertEqual(cst_timezone.abbreviation, "CST")
            self.assertEqual(cst_timezone.tz_name, "Central Standard Time")

    def test_multiple_countries_creation(self):
        """Test creation of multiple countries with shared timezones."""
        with patch(
            "builtins.open", mock_open(read_data=json.dumps(self.multi_country_data))
        ):
            call_command("seed-countries")

            self.assertEqual(Country.objects.count(), 2)
            self.assertEqual(TimeZone.objects.count(), 3)

            usa = Country.objects.get(iso3="USA")
            uk = Country.objects.get(iso3="GBR")

            self.assertEqual(usa.timezones.count(), 2)
            self.assertEqual(uk.timezones.count(), 1)

            gmt_timezone = TimeZone.objects.get(zone_name="Europe/London")
            self.assertIn(gmt_timezone, uk.timezones.all())

    def test_safe_mode_option(self):
        """Test the --safe-mode option with sample data."""
        out = StringIO()
        call_command("seed-countries", "--safe-mode", stdout=out)
        output = out.getvalue()

        self.assertIn("Using safe mode with sample data", output)
        self.assertIn("Successfully seeded", output)

        self.assertEqual(Country.objects.count(), 2)
        self.assertEqual(TimeZone.objects.count(), 3)

        usa = Country.objects.get(iso3="USA")
        canada = Country.objects.get(iso3="CAN")

        self.assertEqual(usa.name, "United States")
        self.assertEqual(canada.name, "Canada")

    def test_country_properties(self):
        """Test that country model properties work correctly after seeding."""
        with patch("builtins.open", mock_open(read_data=json.dumps(self.sample_data))):
            call_command("seed-countries")

            country = Country.objects.get(iso3="USA")

            timezone_list = country.timezone_list
            self.assertEqual(len(timezone_list), 2)
            self.assertIn("America/New_York", timezone_list)
            self.assertIn("America/Chicago", timezone_list)

            self.assertEqual(country.flag, "🇺🇸")

    def test_duplicate_timezone_handling(self):
        """Test that duplicate timezones are handled correctly."""

        duplicate_tz_data = [
            {
                "name": "Country 1",
                "iso2": "C1",
                "iso3": "CO1",
                "timezones": [
                    {
                        "zoneName": "America/New_York",
                        "gmtOffset": -18000,
                        "gmtOffsetName": "UTC-05:00",
                        "abbreviation": "EST",
                        "tzName": "Eastern Standard Time",
                    }
                ],
            },
            {
                "name": "Country 2",
                "iso2": "C2",
                "iso3": "CO2",
                "timezones": [
                    {
                        "zoneName": "America/New_York",
                        "gmtOffset": -18000,
                        "gmtOffsetName": "UTC-05:00",
                        "abbreviation": "EST",
                        "tzName": "Eastern Standard Time",
                    }
                ],
            },
        ]

        with patch("builtins.open", mock_open(read_data=json.dumps(duplicate_tz_data))):
            call_command("seed-countries")

            self.assertEqual(Country.objects.count(), 2)
            self.assertEqual(TimeZone.objects.count(), 1)

            timezone = TimeZone.objects.get(zone_name="America/New_York")
            self.assertEqual(timezone.countries.count(), 2)
