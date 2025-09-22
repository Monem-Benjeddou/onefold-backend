import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    BooleanFilter,
    NumberFilter,
    UUIDFilter,
)
from django.utils.translation import get_language

from apps.countries.models import Country
from apps.countries.utils import get_country_translation


class CountryFilterSet(FilterSet):
    """
    FilterSet for Country model.

    Provides filtering capabilities for Country objects with various filter options.
    """

    name = CharFilter(
        method="filter_name",
        help_text=_(
            "Filter countries by name in English or Arabic (case-insensitive, contains)"
        ),
    )
    iso2 = CharFilter(
        field_name="iso2",
        lookup_expr="iexact",
        help_text=_("Filter countries by ISO2 code (case-insensitive, exact match)"),
    )
    iso3 = CharFilter(
        field_name="iso3",
        lookup_expr="iexact",
        help_text=_("Filter countries by ISO3 code (case-insensitive, exact match)"),
    )
    phone_code = CharFilter(
        field_name="phone_code",
        lookup_expr="icontains",
        help_text=_("Filter countries by phone code (case-insensitive, contains)"),
    )
    capital = CharFilter(
        field_name="capital",
        lookup_expr="icontains",
        help_text=_("Filter countries by capital city (case-insensitive, contains)"),
    )
    region = CharFilter(
        field_name="region",
        lookup_expr="iexact",
        help_text=_("Filter countries by region (case-insensitive, exact match)"),
    )
    subregion = CharFilter(
        field_name="subregion",
        lookup_expr="iexact",
        help_text=_("Filter countries by subregion (case-insensitive, exact match)"),
    )
    currency = CharFilter(
        field_name="currency",
        lookup_expr="iexact",
        help_text=_(
            "Filter countries by currency code (case-insensitive, exact match)"
        ),
    )
    nationality = CharFilter(
        field_name="nationality",
        lookup_expr="icontains",
        help_text=_("Filter countries by nationality (case-insensitive, contains)"),
    )
    is_active = BooleanFilter(
        field_name="is_active",
        help_text=_("Filter countries by active status"),
    )
    has_timezones = BooleanFilter(
        method="filter_has_timezones",
        help_text=_(
            "Filter countries that have timezones (true) or don't have timezones (false)"
        ),
    )
    search = CharFilter(
        method="filter_search",
        help_text=_(
            "Search across name (in English or Arabic), ISO codes, capital, region, and nationality fields"
        ),
    )

    def filter_name(self, queryset, name, value):
        """
        Filter countries by name in English or Arabic.

        This method checks if the provided value matches either the English name
        or its Arabic translation.
        """
        if not value:
            return queryset

        english_matches = queryset.filter(name__icontains=value)

        current_language = get_language()
        all_countries = queryset.exclude(
            pk__in=english_matches.values_list("pk", flat=True)
        )
        arabic_matches_ids = []

        for country in all_countries:
            arabic_name = get_country_translation(country.name, "ar")
            if value.lower() in arabic_name.lower():
                arabic_matches_ids.append(country.pk)

        if arabic_matches_ids:
            arabic_matches = queryset.filter(pk__in=arabic_matches_ids)
            return english_matches | arabic_matches

        return english_matches

    def filter_search(self, queryset, name, value):
        """
        Search across multiple fields: name (in English or Arabic), ISO codes, capital, region, and nationality.
        """
        if not value:
            return queryset

        standard_matches = queryset.filter(
            Q(iso2__icontains=value)
            | Q(iso3__icontains=value)
            | Q(capital__icontains=value)
            | Q(region__icontains=value)
            | Q(subregion__icontains=value)
            | Q(nationality__icontains=value)
            | Q(currency__icontains=value)
            | Q(currency_name__icontains=value)
        )

        name_matches = self.filter_name(queryset, "name", value)

        return (standard_matches | name_matches).distinct()

    def filter_has_timezones(self, queryset, name, value):
        """
        Filter countries that have timezones (true) or don't have timezones (false).
        """
        if value is None:
            return queryset
        if value:
            return queryset.filter(timezones__isnull=False).distinct()
        return queryset.filter(timezones__isnull=True)

    class Meta:
        model = Country
        fields = [
            "name",
            "iso2",
            "iso3",
            "phone_code",
            "capital",
            "region",
            "subregion",
            "currency",
            "nationality",
            "is_active",
            "has_timezones",
            "search",
        ]
