from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    

    path('api/v1/auth/', include('api.apps.accounts.auth.urls')),
    path('api/v1/founders/', include('api.apps.accounts.founder.urls')),
    path('api/v1/companies/', include('api.apps.company.urls')),
    path('api/v1/stakeholders/', include('api.apps.stakeholder.urls')),
    path('api/v1/competitors/', include('api.apps.competitor.urls')),
    path('api/v1/revenue/', include('api.apps.revenue.urls')),
    path('api/v1/funding/', include('api.apps.funding.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
