"""Admin URL configuration."""

from django.urls import path
from . import university_admin_views, deployment_views, admin_views, admin_console_views
from mydak import seller_views

# Admin subdomain URLs (for https://admin.smw.pgwiz.cloud/)
admin_subdomain_patterns = [
    # Admin console URLs (more specific - must come first before catch-all)
    path('console/domains/', admin_console_views.domains_console_view, name='admin_console_domains'),
    path('console/domains/<int:shop_id>/ssl/', admin_console_views.add_ssl_for_shop_view, name='admin_add_ssl'),
    path('console/domains/<int:shop_id>/status/', admin_console_views.ssl_status_view, name='admin_ssl_status'),
    # Dashboard and user-specific paths
    path('dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard_full'),
    path('<str:username>/dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard_user_full'),
    path('<str:username>/shops/', admin_views.admin_shops_view, name='admin_shops'),
    path('<str:username>/shop/<int:shop_id>/', admin_views.admin_shop_detail_view, name='admin_shop_detail'),
    # Catch-all for root and generic username paths (must come last)
    path('<str:username>/', admin_views.admin_dashboard_view, name='admin_dashboard_user'),
    path('', admin_views.admin_dashboard_view, name='admin_dashboard'),
]

# University admin URLs
admin_patterns = [
    path('university/dashboard/', university_admin_views.university_dashboard_view, name='university_dashboard'),
    path('university/shops/', university_admin_views.university_shops_view, name='university_shops'),
    path('university/listings/', university_admin_views.university_listings_view, name='university_listings'),
    path('university/analytics/', university_admin_views.university_analytics_view, name='university_analytics'),
]

# Seller dashboard URLs
seller_patterns = [
    path('seller/dashboard/', seller_views.seller_dashboard_view, name='seller_dashboard'),
    path('seller/listings/', seller_views.seller_listings_view, name='seller_listings'),
    path('seller/messages/', seller_views.seller_messages_view, name='seller_messages'),
    path('seller/analytics/', seller_views.seller_analytics_view, name='seller_analytics'),
    path('seller/insights/', seller_views.seller_insights_view, name='seller_insights'),
    path('seller/settings/', seller_views.seller_settings_view, name='seller_settings'),
]

# Deployment and site admin URLs
deployment_patterns = [
    path('deployment/dashboard/', deployment_views.deployment_dashboard_view, name='deployment_dashboard'),
    path('deployment/update/', deployment_views.trigger_site_update_view, name='trigger_site_update'),
    path('deployment/logs/', deployment_views.get_deployment_logs_view, name='get_deployment_logs'),
]

urlpatterns = admin_patterns + seller_patterns + deployment_patterns
