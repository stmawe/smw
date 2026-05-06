"""
Tenant URL configuration for UniMarket.
These URLs are used for individual tenant (university/location/shop) subdomains.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import admin URL patterns for admin subdomain
from app.admin_urls import admin_subdomain_patterns, admin_crud_patterns

# Shop routing views — handle /{shop_slug}/ and / within a user's subdomain
from mydak import shop_routing_views

urlpatterns = admin_subdomain_patterns + admin_crud_patterns + [
    path('admin/', admin.site.urls),

    # Shop path routing — must come after admin patterns
    # / → root shop storefront or user profile page
    path('', shop_routing_views.tenant_root_view, name='tenant_root'),
    # /{shop_slug}/ → specific shop storefront
    path('<slug:shop_slug>/', shop_routing_views.shop_storefront_view, name='shop_storefront'),

    # Tenant-scoped shop management (dashboard, listings, payments, etc.)
    path('', include('mydak.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
