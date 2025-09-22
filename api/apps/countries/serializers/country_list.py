from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import logging

from ..models import Country
from .common import TimeZoneSerializer

logger = logging.getLogger(__name__)


class CountryLightSerializer(serializers.ModelSerializer):
    """
    Light serializer for country listing.
    Returns basic country information for list views.
    """

    name = serializers.SerializerMethodField()
    flag = serializers.CharField(source="emoji", read_only=True)

    def get_name(self, obj):
        """Get translated country name."""
        from apps.countries import constants

        country_name = obj.name
        return _(country_name)

    class Meta:
        model = Country
        fields = [
            "id",
            "_id",
            "name",
            "iso2",
            "iso3",
            "phone_code",
            "capital",
            "region",
            "subregion",
            "flag",
            "is_active",
        ]


class CountryFullSerializer(serializers.ModelSerializer):
    """
    Full serializer for country listing with all details.
    Returns complete country information including timezones.
    """

    timezones = TimeZoneSerializer(many=True, read_only=True)
    name = serializers.SerializerMethodField()
    flag = serializers.CharField(source="emoji", read_only=True)
    timezone_count = serializers.SerializerMethodField()

    def get_name(self, obj):
        """Get translated country name."""
        from apps.countries import constants

        country_name = obj.name
        return _(country_name)

    def get_timezone_count(self, obj):
        """Return the number of timezones in this country."""
        return obj.timezones.count()

    class Meta:
        model = Country
        fields = [
            "id",
            "_id",
            "name",
            "iso2",
            "iso3",
            "numeric_code",
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
            "latitude",
            "longitude",
            "flag",
            "is_active",
            "timezones",
            "timezone_count",
            "created",
            "updated",
        ]
