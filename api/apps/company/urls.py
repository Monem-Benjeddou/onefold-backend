from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.company.views import (
    StartupProfileViewSet,
    DevelopmentStageViewSet,
    StartupDevelopmentStageViewSet,
    CompanyMemberViewSet,
    TargetedMarketViewSet
)
from apps.company.views.startup_service_product import StartupServiceProductViewSet

router = DefaultRouter()
router.register(r'startups', StartupProfileViewSet, basename='startup-profile')
router.register(r'development-stages', DevelopmentStageViewSet, basename='development-stage')
router.register(r'startup-development-stages', StartupDevelopmentStageViewSet, basename='startup-development-stage')
router.register(r'members', CompanyMemberViewSet, basename='company-member')
router.register(r'targeted-markets', TargetedMarketViewSet, basename='targeted-market')
router.register(r'services-products', StartupServiceProductViewSet, basename='startup-service-product')

urlpatterns = [
    path('', include(router.urls)),
]
