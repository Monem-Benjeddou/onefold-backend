from .serializers.common import TimeZoneSerializer, StateSerializer, CitySerializer
from .serializers.country_list import CountryLightSerializer, CountryFullSerializer
from .serializers.country_detail import CountryDetailSerializer
from .serializers.city_list import CityLightSerializer, CityFullSerializer
from .serializers.school_list import SchoolLightSerializer
from .serializers.school_detail import SchoolDetailSerializer

SchoolSerializer = SchoolDetailSerializer

__all__ = [
    "TimeZoneSerializer",
    "CitySerializer",
    "StateSerializer",
    "CountryLightSerializer",
    "CountryFullSerializer",
    "CountryDetailSerializer",
    "CityFullSerializer",
    "CityLightSerializer",
    "SchoolLightSerializer",
    "SchoolSerializer",
    "SchoolDetailSerializer",
]
