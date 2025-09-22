from rest_framework import serializers
from ..models import TimeZone


class TimeZoneSerializer(serializers.ModelSerializer):
    """Serializer for TimeZone model."""

    country_count = serializers.SerializerMethodField()

    class Meta:
        model = TimeZone
        fields = [
            "id",
            "_id",
            "zone_name",
            "gmt_offset",
            "gmt_offset_name",
            "abbreviation",
            "tz_name",
            "country_count",
        ]
        read_only_fields = ["id", "_id", "country_count"]

    def get_country_count(self, obj):
        """Return the number of countries using this timezone."""
        return obj.countries.count()
