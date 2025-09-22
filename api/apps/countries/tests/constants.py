"""
Test constants for countries app tests.
"""

TEST_COUNTRY_DATA = {
    "name": "Test Country",
    "iso3": "TST",
    "iso2": "TS",
    "numeric_code": "999",
    "phone_code": "+999",
    "capital": "Test Capital",
    "currency": "TST",
    "currency_name": "Test Currency",
    "currency_symbol": "T$",
    "tld": ".test",
    "native": "Test Native",
    "region": "Test Region",
    "subregion": "Test Subregion",
    "nationality": "Test Nationality",
    "latitude": "12.345678",
    "longitude": "98.765432",
    "emoji": "🏳️",
    "is_active": True,
}


TEST_TIMEZONE_DATA = {
    "zone_name": "Test/Timezone",
    "gmt_offset": 0,
    "gmt_offset_name": "UTC+00:00",
    "abbreviation": "UTC",
    "tz_name": "Test Timezone",
}


COUNTRIES_LIST_URL = "/api/v1/countries/"
COUNTRY_DETAIL_URL = "/api/v1/countries/{id}/"


RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_PERIOD = 60
