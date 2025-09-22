from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.revenue.views import (
    RevenueModelViewSet,
    RevenueStreamViewSet
)

router = DefaultRouter()
router.register(r'models', RevenueModelViewSet, basename='revenue-model')
router.register(r'streams', RevenueStreamViewSet, basename='revenue-stream')

urlpatterns = [
    path('', include(router.urls)),
]
