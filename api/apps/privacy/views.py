from rest_framework import generics
from drf_spectacular.utils import extend_schema

from .models import PrivacyPolicyPoint
from .serializers import PrivacyPolicyPointSerializer
from core.abstract.paginations import MetaPageNumberPagination


@extend_schema(tags=["Privacy"])
class PrivacyPolicyPointListView(generics.ListAPIView):
    queryset = PrivacyPolicyPoint.objects.all()
    pagination_class = MetaPageNumberPagination
    serializer_class = PrivacyPolicyPointSerializer
