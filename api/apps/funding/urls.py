from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.funding.views import (
    FundingTargetViewSet,
    RaisedFundViewSet
)

router = DefaultRouter()
router.register(r'targets', FundingTargetViewSet, basename='funding-target')
router.register(r'raised-funds', RaisedFundViewSet, basename='raised-fund')

urlpatterns = [
    path('', include(router.urls)),
]
