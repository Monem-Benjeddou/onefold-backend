from django.contrib import admin

from .models import Country, TimeZone


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """Admin configuration for Country model."""

    list_display = [
        "name",
        "iso3",
        "iso2",
        "phone_code",
        "capital",
        "currency",
        "currency_name",
        "currency_symbol",
        "tld",
        "native",
        "region",
        "subregion",
        "is_active",
        "created",
    ]
    list_filter = ["region", "subregion", "is_active", "created", "updated"]
    search_fields = [
        "name",
        "iso3",
        "iso2",
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
    ]
    ordering = ["name"]
    readonly_fields = ["created", "updated"]
    filter_horizontal = ["timezones"]
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "native", "capital", "nationality", "is_active")},
        ),
        ("ISO Codes", {"fields": ("iso2", "iso3", "numeric_code", "phone_code")}),
        (
            "Currency Information",
            {"fields": ("currency", "currency_name", "currency_symbol")},
        ),
        (
            "Location Information",
            {"fields": ("region", "subregion", "latitude", "longitude", "emoji")},
        ),
        ("Technical Information", {"fields": ("tld", "timezones")}),
        (
            "Metadata",
            {"fields": ("created", "updated"), "classes": ("collapse",)},
        ),
    )


@admin.register(TimeZone)
class TimeZoneAdmin(admin.ModelAdmin):
    """Admin configuration for TimeZone model."""

    list_display = [
        "zone_name",
        "gmt_offset",
        "gmt_offset_name",
        "abbreviation",
        "tz_name",
        "country_count",
    ]
    list_filter = ["gmt_offset"]
    search_fields = [
        "zone_name",
        "gmt_offset_name",
        "abbreviation",
        "tz_name",
    ]
    ordering = ["zone_name"]

    def country_count(self, obj):
        """Return the number of countries using this timezone."""
        return obj.countries.count()

    country_count.short_description = "Countries Count"
