"""
Factory classes for Countries app models.
"""

import factory
from factory.django import DjangoModelFactory
from apps.countries.models import TimeZone, Country


class TimeZoneFactory(DjangoModelFactory):
    """Factory for creating TimeZone instances for testing."""

    class Meta:
        model = TimeZone
        django_get_or_create = ("zone_name",)

    zone_name = factory.Sequence(lambda n: f"Test/Timezone{n}")
    gmt_offset = factory.Faker("random_int", min=-12, max=14)
    gmt_offset_name = factory.LazyAttribute(
        lambda obj: f"GMT{'+' if obj.gmt_offset >= 0 else ''}{obj.gmt_offset:02d}:00"
    )
    abbreviation = factory.Faker("lexify", text="???")
    tz_name = factory.LazyAttribute(lambda obj: obj.zone_name.split("/")[-1])


class CountryFactory(DjangoModelFactory):
    """Factory for creating Country instances for testing."""

    class Meta:
        model = Country
        django_get_or_create = ("name",)

    name = factory.Faker("country")
    iso3 = factory.Faker("country_code", representation="alpha-3")
    iso2 = factory.Faker("country_code", representation="alpha-2")
    numeric_code = factory.Faker("numerify", text="###")
    phone_code = factory.Faker("numerify", text="+###")
    capital = factory.Faker("city")
    currency = factory.Faker("currency_code")
    currency_name = factory.Faker("currency_name")
    currency_symbol = factory.Faker("currency_symbol")
    tld = factory.LazyAttribute(
        lambda obj: f".{obj.iso2.lower()}" if obj.iso2 else ".xx"
    )
    native = factory.Faker("country")
    region = factory.Faker("word")
    subregion = factory.Faker("word")
    nationality = factory.LazyAttribute(lambda obj: f"{obj.name}ian")
    latitude = factory.Faker("latitude")
    longitude = factory.Faker("longitude")
    emoji = factory.LazyAttribute(lambda obj: "🏳️" if obj.iso2 else "🌍")
    is_active = True

    @factory.post_generation
    def timezones(self, create, extracted, **kwargs):
        """Add timezones to the country after creation."""
        if not create:
            return

        if extracted:
            for timezone in extracted:
                self.timezones.add(timezone)
        else:

            timezone = TimeZoneFactory()
            self.timezones.add(timezone)
