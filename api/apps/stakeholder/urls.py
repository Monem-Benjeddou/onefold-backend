from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.stakeholder.views import (
    StakeholderViewSet,
    InvestorViewSet
)

router = DefaultRouter()
router.register(r'stakeholders', StakeholderViewSet, basename='stakeholder')
router.register(r'investors', InvestorViewSet, basename='investor')

urlpatterns = [
    path('', include(router.urls)),
]
