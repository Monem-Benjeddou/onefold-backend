from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "accounts"

urlpatterns = [
    path("config/", views.AuthConfigView.as_view(), name="config"),
    # Password
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("password/forgot/", views.ForgotPasswordView.as_view(), name="password-forgot"),
    path("password/reset/", views.ResetPasswordView.as_view(), name="password-reset"),
    path("password/change/", views.ChangePasswordView.as_view(), name="password-change"),
    # Emailed links
    path("magic-link/", views.MagicLinkRequestView.as_view(), name="magic-link"),
    path("magic-link/verify/", views.MagicLinkVerifyView.as_view(), name="magic-link-verify"),
    path("email/verify/", views.VerifyEmailView.as_view(), name="email-verify"),
    path("email/resend/", views.ResendVerificationView.as_view(), name="email-resend"),
    # GitHub / Google
    path("oauth/<slug:provider>/start/", views.OAuthStartView.as_view(), name="oauth-start"),
    path(
        "oauth/<slug:provider>/callback/",
        views.OAuthCallbackView.as_view(),
        name="oauth-callback",
    ),
    # Sessions
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("sessions/", views.SessionListView.as_view(), name="sessions"),
    path(
        "sessions/revoke-others/",
        views.RevokeOtherSessionsView.as_view(),
        name="sessions-revoke-others",
    ),
    path("sessions/<uuid:pk>/", views.SessionDetailView.as_view(), name="session-detail"),
    # Development
    path("demo/", views.DemoSignInView.as_view(), name="demo"),
    path("me/", views.MeView.as_view(), name="me"),
]
