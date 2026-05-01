"""
Tenant URL configuration for UniMarket.
These URLs are used for individual tenant (university/location/shop) subdomains.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import admin URL patterns for admin subdomain
from app.admin_urls import admin_subdomain_patterns

urlpatterns = admin_subdomain_patterns + [
    path('admin/', admin.site.urls),
    path('', include('mydak.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
