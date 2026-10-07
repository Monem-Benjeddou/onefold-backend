from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from . import views

app_name = "accounts"

urlpatterns = [
    path("magic-link/", views.MagicLinkRequestView.as_view(), name="magic-link"),
    path("magic-link/verify/", views.MagicLinkVerifyView.as_view(), name="magic-link-verify"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", TokenBlacklistView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
]
