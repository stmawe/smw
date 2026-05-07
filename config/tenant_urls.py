"""
Tenant URL configuration for UniMarket.
These URLs are used for individual tenant (user subdomain) requests:
    {username}.smw.pgwiz.cloud/

django-tenants middleware resolves the tenant schema from the hostname,
then this URL conf dispatches within that schema.

NOTE: Admin patterns are NOT included here — they are only served on
admin.smw.pgwiz.cloud via AdminSubdomainMiddleware + app.admin_urls.
"""

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from mydak import shop_routing_views

urlpatterns = [
    # /dashboard/ → seller dashboard (login required) — MUST be before <slug:shop_slug>/
    path('dashboard/', shop_routing_views.seller_dashboard_view, name='seller_dashboard'),

    # / → root shop storefront (if Tier 1) or user profile page
    path('', shop_routing_views.tenant_root_view, name='tenant_root'),

    # /{shop_slug}/ → specific shop storefront
    path('<slug:shop_slug>/', shop_routing_views.shop_storefront_view, name='shop_storefront'),

    # Tenant-scoped shop management (listings, payments, messaging, etc.)
    path('', include('mydak.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
