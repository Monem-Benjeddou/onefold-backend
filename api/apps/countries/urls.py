from django.urls import path

from .views import (
    CountryListView,
    CountryDetailView,
)

app_name = "countries"

urlpatterns = [
    path("", CountryListView.as_view(), name="country-list"),
    path("<uuid:id>/", CountryDetailView.as_view(), name="country-detail"),
]


"""
URL Documentation:
==================================================

Countries API Endpoints:
------------------------

GET /api/v1/countries/
Name: country-list
View: CountryListView
Description: List all countries with filtering and pagination support
--------------------------------------------------

GET /api/v1/countries/<uuid:id>/
Name: country-detail
View: CountryDetailView  
Description: Retrieve detailed information about a specific country
--------------------------------------------------

Available Query Parameters for country-list:
- search: Search in country name, capital, region, etc.
- region: Filter by region
- subregion: Filter by subregion
- is_active: Filter by active status (true/false)
- ordering: Order by fields (name, iso2, iso3, region, etc.)

Example API calls:
- GET /api/v1/countries/ - List all countries
- GET /api/v1/countries/?search=united - Search for countries
- GET /api/v1/countries/?region=Europe - Filter by region
- GET /api/v1/countries/?is_active=true - Only active countries
- GET /api/v1/countries/?ordering=name - Order by name
- GET /api/v1/countries/<uuid>/ - Get specific country details
"""
