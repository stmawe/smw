"""Admin URL configuration."""

from django.urls import path
from . import university_admin_views, deployment_views
from mydak import seller_views

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
