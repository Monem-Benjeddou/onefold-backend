from django.db import models
from core.abstract.models import AbstractAutoIncrementModel


class TimeZone(AbstractAutoIncrementModel):
    """Model representing a timezone with its properties."""

    zone_name = models.CharField(max_length=150, unique=True, null=False, blank=False)
    gmt_offset = models.IntegerField(null=True, blank=True)
    gmt_offset_name = models.CharField(max_length=50, null=True, blank=True)
    abbreviation = models.CharField(max_length=20, null=True, blank=True)
    tz_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.zone_name or "Unknown TimeZone"

    class Meta:
        ordering = ["zone_name"]
        verbose_name = "Time Zone"
        verbose_name_plural = "Time Zones"


class Country(AbstractAutoIncrementModel):
    """Model representing a country with its properties and relationships."""

    name = models.CharField(max_length=255, unique=True)
    iso3 = models.CharField(
        max_length=3,
        unique=True,
        null=True,
        blank=True,
        help_text="ISO 3166-1 alpha-3 code",
    )
    iso2 = models.CharField(
        max_length=2,
        unique=True,
        null=True,
        blank=True,
        help_text="ISO 3166-1 alpha-2 code",
    )
    numeric_code = models.CharField(
        max_length=5, null=True, blank=True, help_text="ISO 3166-1 numeric code"
    )
    phone_code = models.CharField(
        max_length=10, null=True, blank=True, help_text="International calling code"
    )
    capital = models.CharField(max_length=150, null=True, blank=True)
    currency = models.CharField(
        max_length=100, null=True, blank=True, help_text="Currency code (e.g., USD)"
    )
    currency_name = models.CharField(max_length=100, null=True, blank=True)
    currency_symbol = models.CharField(max_length=10, null=True, blank=True)
    tld = models.CharField(
        max_length=10, null=True, blank=True, help_text="Top-level domain"
    )
    native = models.CharField(
        max_length=255, null=True, blank=True, help_text="Native name"
    )
    region = models.CharField(max_length=100, null=True, blank=True)
    subregion = models.CharField(max_length=100, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Latitude coordinate",
    )
    longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Longitude coordinate",
    )
    emoji = models.CharField(max_length=20, null=True, blank=True)
    timezones = models.ManyToManyField(
        TimeZone,
        related_name="countries",
        blank=True,
        help_text="Timezones available in this country",
    )

    is_active = models.BooleanField(
        default=True, help_text="Whether this country is active for selection"
    )

    def __str__(self):
        return self.name or "Unknown Country"

    @property
    def timezone_list(self):
        """Return a list of timezone names for this country."""
        return list(self.timezones.values_list("zone_name", flat=True))

    @property
    def flag(self):
        """Return the country flag emoji."""
        return self.emoji or ""

    class Meta:
        ordering = ["name"]
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["iso2"]),
            models.Index(fields=["iso3"]),
            models.Index(fields=["region"]),
            models.Index(fields=["is_active"]),
        ]
