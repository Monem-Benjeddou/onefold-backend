import json
from django.core.management.base import BaseCommand
import logging
from django.db import transaction
from apps.countries.models import Country, TimeZone
import os
import re

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Load country data from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--safe-mode",
            action="store_true",
            help="Use a safe sample data for testing if the real data is corrupted",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-seeding even if countries already exist",
        )

    def handle(self, *args, **kwargs):
        safe_mode = kwargs.get("safe_mode", False)
        force = kwargs.get("force", False)

        if Country.objects.exists() and not force:
            self.stdout.write(
                self.style.SUCCESS("Countries already exist. Use --force to re-seed.")
            )
            return

        if force:
            self.stdout.write(
                self.style.WARNING("Force mode: Clearing existing data...")
            )
            Country.objects.all().delete()
            TimeZone.objects.all().delete()

        if safe_mode:
            countries = self._get_sample_data()
            self.stdout.write(self.style.WARNING("Using safe mode with sample data"))
        else:
            file_path = "apps/countries/static/countries.json"
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)

                        if (
                            isinstance(data, list)
                            and len(data) > 0
                            and isinstance(data[0], list)
                        ):
                            countries = data[0]
                        else:
                            countries = data
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON: {str(e)}")
                        self.stderr.write(
                            self.style.ERROR(
                                f"Failed to decode JSON: {str(e)}\n"
                                f"Try using --safe-mode to use sample data instead."
                            )
                        )
                        return
            except FileNotFoundError:
                logger.error(f"File not found: {file_path}")
                self.stderr.write(
                    self.style.ERROR(
                        f"File not found: {file_path}\n"
                        f"Try using --safe-mode to use sample data instead."
                    )
                )
                return

        total_countries = len(countries)
        self.stdout.write(f"Found {total_countries} countries in the data")

        with transaction.atomic():

            all_timezones = {}
            for country_data in countries:
                for tz_data in country_data.get("timezones", []):
                    zone_name = tz_data.get("zoneName", "")
                    if zone_name and zone_name not in all_timezones:
                        all_timezones[zone_name] = {
                            "gmt_offset": tz_data.get("gmtOffset", 0),
                            "gmt_offset_name": tz_data.get("gmtOffsetName", ""),
                            "abbreviation": tz_data.get("abbreviation", ""),
                            "tz_name": tz_data.get("tzName", ""),
                        }

            timezone_objects = []
            for zone_name, tz_data in all_timezones.items():
                timezone_objects.append(
                    TimeZone(
                        zone_name=zone_name,
                        gmt_offset=tz_data["gmt_offset"],
                        gmt_offset_name=tz_data["gmt_offset_name"],
                        abbreviation=tz_data["abbreviation"],
                        tz_name=tz_data["tz_name"],
                    )
                )

            created_timezones = {}
            if timezone_objects:
                self.stdout.write(f"Creating {len(timezone_objects)} timezones")
                TimeZone.objects.bulk_create(timezone_objects, ignore_conflicts=True)

                for tz in TimeZone.objects.all():
                    created_timezones[tz.zone_name] = tz

            country_objects = []
            for country_data in countries:
                iso3 = country_data.get("iso3", "")
                if not iso3:
                    continue

                country = Country(
                    name=country_data.get("name", ""),
                    iso2=country_data.get("iso2", ""),
                    iso3=iso3,
                    numeric_code=country_data.get("numeric_code", ""),
                    phone_code=country_data.get("phone_code", ""),
                    capital=country_data.get("capital", ""),
                    currency=country_data.get("currency", ""),
                    currency_name=country_data.get("currency_name", ""),
                    currency_symbol=country_data.get("currency_symbol", ""),
                    tld=country_data.get("tld", ""),
                    native=country_data.get("native", ""),
                    region=country_data.get("region", ""),
                    subregion=country_data.get("subregion", ""),
                    nationality=country_data.get("nationality", ""),
                    latitude=country_data.get("latitude", None),
                    longitude=country_data.get("longitude", None),
                    emoji=country_data.get("emoji", ""),
                    is_active=True,
                )
                country_objects.append(country)

            self.stdout.write(f"Creating {len(country_objects)} countries")
            Country.objects.bulk_create(country_objects, ignore_conflicts=True)

            created_countries = {}
            for country in Country.objects.all():
                created_countries[country.iso3] = country

            self.stdout.write("Establishing timezone relationships")
            for country_data in countries:
                iso3 = country_data.get("iso3", "")
                if iso3 not in created_countries:
                    continue

                country = created_countries[iso3]

                for tz_data in country_data.get("timezones", []):
                    zone_name = tz_data.get("zoneName", "")
                    if zone_name in created_timezones:
                        country.timezones.add(created_timezones[zone_name])

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded {len(country_objects)} countries and {len(timezone_objects)} timezones"
            )
        )

    def _get_sample_data(self):
        """Return sample data for testing purposes."""
        return [
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
            },
            {
                "name": "Canada",
                "iso2": "CA",
                "iso3": "CAN",
                "numeric_code": "124",
                "phone_code": "1",
                "capital": "Ottawa",
                "currency": "CAD",
                "currency_name": "Canadian dollar",
                "currency_symbol": "$",
                "tld": ".ca",
                "native": "Canada",
                "region": "Americas",
                "subregion": "Northern America",
                "nationality": "Canadian",
                "latitude": 56.130366,
                "longitude": -106.346771,
                "emoji": "🇨🇦",
                "timezones": [
                    {
                        "zoneName": "America/Toronto",
                        "gmtOffset": -18000,
                        "gmtOffsetName": "UTC-05:00",
                        "abbreviation": "EST",
                        "tzName": "Eastern Standard Time",
                    },
                ],
            },
        ]
