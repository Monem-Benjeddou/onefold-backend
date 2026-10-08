from django.urls import path

from . import views

app_name = "workspace"

urlpatterns = [
    path("workspace/", views.WorkspaceView.as_view(), name="workspace"),
    path("onboarding/", views.OnboardingView.as_view(), name="onboarding"),
    path("onboarding/draft/", views.OnboardingDraftView.as_view(), name="onboarding-draft"),
]
