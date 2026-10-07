from django.urls import path

from . import views

app_name = "learning"

urlpatterns = [
    path("paths/current/", views.CurrentPathView.as_view(), name="path-current"),
    path("enrollment/", views.EnrollmentView.as_view(), name="enrollment"),
    path("enrollment/steps/<slug:slug>/", views.StepDetailView.as_view(), name="step-detail"),
    path("enrollment/steps/<slug:slug>/start/", views.StepStartView.as_view(), name="step-start"),
    path(
        "enrollment/steps/<slug:slug>/complete/",
        views.StepCompleteView.as_view(),
        name="step-complete",
    ),
]
