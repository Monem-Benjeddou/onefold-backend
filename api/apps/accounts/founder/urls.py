from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.accounts.founder.views import (
    FounderProfileViewSet,
    EducationViewSet,
    PreviousCompanyViewSet
)

router = DefaultRouter()
router.register(r'profiles', FounderProfileViewSet, basename='founder-profile')
router.register(r'education', EducationViewSet, basename='education')
router.register(r'previous-companies', PreviousCompanyViewSet, basename='previous-company')

urlpatterns = [
    path('', include(router.urls)),
]
