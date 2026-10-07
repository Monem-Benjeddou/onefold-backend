from django.urls import path

from .views import CheckRunDetailView

app_name = "verification"

urlpatterns = [
    path("<uuid:pk>/", CheckRunDetailView.as_view(), name="check-detail"),
]
