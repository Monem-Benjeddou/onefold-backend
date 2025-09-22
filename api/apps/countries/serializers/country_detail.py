from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import logging

from ..models import Country
from .common import TimeZoneSerializer

logger = logging.getLogger(__name__)


class CountryDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for country detail view.
    Returns complete country information for individual country retrieval.
    """

    timezones = TimeZoneSerializer(many=True, read_only=True)
    name = serializers.SerializerMethodField()
    flag = serializers.CharField(source="emoji", read_only=True)
    timezone_count = serializers.SerializerMethodField()
    timezone_list = serializers.SerializerMethodField()

    def get_name(self, obj):
        """Get translated country name."""
        from apps.countries import constants

        country_name = obj.name
        return _(country_name)

    def get_timezone_count(self, obj):
        """Return the number of timezones in this country."""
        return obj.timezones.count()

    def get_timezone_list(self, obj):
        """Return a simple list of timezone names."""
        return obj.timezone_list

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
            "timezone_list",
            "created",
            "updated",
        ]
        read_only_fields = [
            "id",
            "_id",
            "created",
            "updated",
            "timezone_count",
            "timezone_list",
            "flag",
        ]
