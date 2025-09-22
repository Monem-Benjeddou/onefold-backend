from django.urls import path
from .views import PrivacyPolicyPointListView

urlpatterns = [
    path("", PrivacyPolicyPointListView.as_view(), name="privacy-policy-list"),
]
