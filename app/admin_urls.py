"""Admin URL configuration."""

from django.urls import path
from . import university_admin_views, deployment_views, admin_views, admin_console_views, admin_crud_views, admin_advanced_views, admin_api
from mydak import seller_views

# Admin subdomain URLs (for https://admin.smw.pgwiz.cloud/)
# This becomes the urlpatterns when middleware routes to admin subdomain
admin_subdomain_base = [
    # Admin login (root path - shows login page for unauthenticated users)
    path('', admin_views.admin_login_view, name='admin_login'),
    path('login/', admin_views.admin_login_view, name='admin_login_explicit'),
    
    # Admin console URLs (requires authentication)
    path('console/domains/', admin_console_views.domains_console_view, name='admin_console_domains'),
    path('console/domains/<int:shop_id>/ssl/', admin_console_views.add_ssl_for_shop_view, name='admin_add_ssl'),
    path('console/domains/<int:shop_id>/status/', admin_console_views.ssl_status_view, name='admin_ssl_status'),
    
    # Dashboard and user-specific paths (requires authentication)
    path('dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard_full'),
    path('<str:username>/dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard_user_full'),
    path('<str:username>/shops/', admin_views.admin_shops_view, name='admin_shops'),
    path('<str:username>/shop/<int:shop_id>/', admin_views.admin_shop_detail_view, name='admin_shop_detail'),
    # Catch-all for generic username paths (must come last)
    path('<str:username>/', admin_views.admin_dashboard_view, name='admin_dashboard_user'),
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

# Admin Panel CRUD URLs (comprehensive admin management)
admin_crud_patterns = [
    # Dashboard
    path('admin/dashboard/', admin_crud_views.admin_dashboard_full, name='admin_dashboard_full'),
    
    # User Management
    path('admin/users/', admin_crud_views.admin_users_list, name='admin_users_list'),
    path('admin/user/create/', admin_crud_views.admin_user_detail, name='admin_user_create'),
    path('admin/user/<int:user_id>/', admin_crud_views.admin_user_detail, name='admin_user_detail'),
    path('admin/user/<int:user_id>/suspend/', admin_crud_views.admin_user_suspend, name='admin_user_suspend'),
    path('admin/user/<int:user_id>/unsuspend/', admin_crud_views.admin_user_unsuspend, name='admin_user_unsuspend'),
    
    # Shop Management
    path('admin/shops/', admin_crud_views.admin_shops_list, name='admin_shops_list'),
    path('admin/shop/create/', admin_crud_views.admin_shop_detail, name='admin_shop_create'),
    path('admin/shop/<int:shop_id>/', admin_crud_views.admin_shop_detail, name='admin_shop_detail'),
    path('admin/shop/<int:shop_id>/ssl/', admin_crud_views.admin_ssl_domain_detail, name='admin_shop_ssl'),
    path('admin/shop/<int:shop_id>/listings/', admin_crud_views.admin_listings_moderation, name='admin_shop_listings'),
    path('admin/shop/<int:shop_id>/analytics/', admin_advanced_views.admin_analytics_dashboard, name='admin_shop_analytics'),
    
    # Listing Moderation
    path('admin/listings/', admin_crud_views.admin_listings_moderation, name='admin_listings_list'),
    path('admin/listings/moderation/', admin_crud_views.admin_listings_moderation, name='admin_listings_moderation'),
    path('admin/listing/<int:listing_id>/', admin_crud_views.admin_listing_detail, name='admin_listing_detail'),
    
    # Category Management
    path('admin/categories/', admin_crud_views.admin_categories_list, name='admin_categories_list'),
    path('admin/category/create/', admin_crud_views.admin_category_create, name='admin_category_create'),
    path('admin/category/<int:category_id>/delete/', admin_crud_views.admin_category_delete, name='admin_category_delete'),
    
    # Transactions
    path('admin/transactions/', admin_crud_views.admin_transactions_list, name='admin_transactions_list'),
    path('admin/transaction/<int:transaction_id>/', admin_advanced_views.admin_analytics_dashboard, name='admin_transaction_detail'),
    
    # Settings & Configuration
    path('admin/settings/', admin_crud_views.admin_settings_view, name='admin_settings_view'),
    path('admin/settings/general/', admin_crud_views.admin_settings_view, name='admin_settings'),
    
    # Theme Management
    path('admin/themes/', admin_crud_views.admin_themes_list, name='admin_themes_list'),
    path('admin/theme/<int:theme_id>/activate/', admin_crud_views.admin_theme_activate, name='admin_theme_activate'),
    
    # Audit Logs
    path('admin/audit-logs/', admin_crud_views.admin_audit_logs, name='admin_audit_logs'),
    
    # SSL & Domain Management
    path('admin/ssl-domains/', admin_crud_views.admin_ssl_domains_list, name='admin_ssl_domains_list'),
    path('admin/ssl-domain/<int:shop_id>/', admin_crud_views.admin_ssl_domain_detail, name='admin_ssl_domain_detail'),
    path('admin/ssl/<int:shop_id>/generate/', admin_crud_views.admin_ssl_generate, name='admin_ssl_generate'),
    path('admin/ssl/<int:shop_id>/renew/', admin_crud_views.admin_ssl_renew, name='admin_ssl_renew'),
    path('admin/ssl/<int:shop_id>/check-status/', admin_crud_views.admin_ssl_check_status, name='admin_ssl_check_status'),
    path('admin/ssl/bulk-generate/', admin_crud_views.admin_ssl_bulk_generate, name='admin_ssl_bulk_generate'),
    
    # Tenant Management (Superuser only)
    path('admin/tenants/', admin_crud_views.admin_tenants_list, name='admin_tenants_list'),
    path('admin/tenant/<int:tenant_id>/', admin_crud_views.admin_tenant_detail, name='admin_tenant_detail'),
    path('admin/tenant/<int:tenant_id>/billing/', admin_crud_views.admin_tenant_update_billing, name='admin_tenant_update_billing'),
    path('admin/tenant/<int:tenant_id>/activate/', admin_crud_views.admin_tenant_activate, name='admin_tenant_activate'),
    path('admin/tenant/<int:tenant_id>/deactivate/', admin_crud_views.admin_tenant_deactivate, name='admin_tenant_deactivate'),
    path('admin/tenant/<int:tenant_id>/domains/', admin_crud_views.admin_tenant_domains, name='admin_tenant_domains'),
    path('admin/tenant/<int:tenant_id>/domain/add/', admin_crud_views.admin_tenant_add_domain, name='admin_tenant_add_domain'),
    path('admin/tenant/<int:tenant_id>/domain/<int:domain_id>/delete/', admin_crud_views.admin_tenant_delete_domain, name='admin_tenant_delete_domain'),
    
    # Theme Management (Enhanced CRUD)
    path('admin/themes/', admin_crud_views.admin_themes_list, name='admin_themes_list'),
    path('admin/theme/<int:theme_id>/', admin_crud_views.admin_theme_detail, name='admin_theme_detail'),
    path('admin/theme/create/', admin_crud_views.admin_theme_create, name='admin_theme_create'),
    path('admin/theme/<int:theme_id>/update/', admin_crud_views.admin_theme_update, name='admin_theme_update'),
    path('admin/theme/<int:theme_id>/activate/', admin_crud_views.admin_theme_activate, name='admin_theme_activate'),
    path('admin/theme/<int:theme_id>/delete/', admin_crud_views.admin_theme_delete, name='admin_theme_delete'),
    path('admin/theme/<int:theme_id>/preview/', admin_crud_views.admin_theme_preview, name='admin_theme_preview'),
    path('admin/theme/<int:theme_id>/publish/', admin_crud_views.admin_theme_publish, name='admin_theme_publish'),
    path('admin/theme/<int:theme_id>/unpublish/', admin_crud_views.admin_theme_unpublish, name='admin_theme_unpublish'),
    
    # Activity Feed & Changelog
    path('admin/activity-feed/', admin_crud_views.admin_activity_feed_view, name='admin_activity_feed_view'),
    path('admin/changelog/', admin_crud_views.admin_changelog_view, name='admin_changelog_view'),
    
    # JSON API Endpoints (for AJAX/modals)
    path('admin/api/user/<int:user_id>/', admin_crud_views.api_user_details, name='api_user_details'),
    path('admin/api/shop/<int:shop_id>/', admin_crud_views.api_shop_details, name='api_shop_details'),
    path('admin/api/listing/<int:listing_id>/', admin_crud_views.api_listing_details, name='api_listing_details'),
    
    # Advanced Features - Moderation & Transaction Management
    path('admin/moderation/', admin_advanced_views.admin_moderation_center, name='admin_moderation_center'),
    path('admin/listing/<int:listing_id>/flag/', admin_advanced_views.admin_flag_listing, name='admin_flag_listing'),
    path('admin/listing/<int:listing_id>/unflag/', admin_advanced_views.admin_unflag_listing, name='admin_unflag_listing'),
    path('admin/user/<int:user_id>/ban-extended/', admin_advanced_views.admin_ban_user_extended, name='admin_ban_user_extended'),
    
    # Transactions & Refunds
    path('admin/transaction/<int:transaction_id>/refund/', admin_advanced_views.admin_process_refund, name='admin_process_refund'),
    
    # Analytics
    path('admin/analytics/', admin_advanced_views.admin_analytics_dashboard, name='admin_analytics_dashboard'),
    
    # Settings
    path('admin/settings/save/', admin_advanced_views.admin_save_settings, name='admin_save_settings'),
    
    # Bulk Operations
    path('admin/listings/bulk-action/', admin_advanced_views.admin_bulk_listing_action, name='admin_bulk_listing_action'),
    path('admin/users/bulk-action/', admin_advanced_views.admin_bulk_user_action, name='admin_bulk_user_action'),
    
    # Activity & Logs
    path('admin/activity-feed/', admin_advanced_views.admin_activity_feed, name='admin_activity_feed'),
    path('admin/audit-log/<int:log_id>/', admin_advanced_views.admin_audit_log_detail, name='admin_audit_log_detail'),
    
    # JSON APIs
    path('admin/api/metrics/', admin_advanced_views.api_dashboard_metrics, name='api_dashboard_metrics'),
    path('admin/api/activity-updates/', admin_advanced_views.api_activity_feed_updates, name='api_activity_feed_updates'),
    
    # REST API Endpoints (comprehensive)
    path('admin/api/users/', admin_api.api_users_list, name='api_users_list'),
    path('admin/api/users/<int:user_id>/update/', admin_api.api_user_update, name='api_user_update'),
    path('admin/api/users/<int:user_id>/permissions/', admin_api.api_user_permissions, name='api_user_permissions'),
    
    path('admin/api/shops/', admin_api.api_shops_list, name='api_shops_list'),
    
    path('admin/api/listings/', admin_api.api_listings_list, name='api_listings_list'),
    path('admin/api/listings/<int:listing_id>/action/', admin_api.api_listing_action, name='api_listing_action'),
    
    path('admin/api/transactions/', admin_api.api_transactions_list, name='api_transactions_list'),
    path('admin/api/transactions/<int:transaction_id>/refund/', admin_api.api_transaction_refund, name='api_transaction_refund'),
    
    path('admin/api/audit-logs/', admin_api.api_audit_logs_list, name='api_audit_logs_list'),
    path('admin/api/audit-logs/<int:log_id>/', admin_api.api_audit_log_detail, name='api_audit_log_detail'),
    
    path('admin/api/analytics/summary/', admin_api.api_analytics_summary, name='api_analytics_summary'),
    path('admin/api/analytics/top-sellers/', admin_api.api_analytics_top_sellers, name='api_analytics_top_sellers'),
    
    path('admin/api/activity-feed/', admin_api.api_activity_feed, name='api_activity_feed'),
]

# Combine admin subdomain patterns with CRUD patterns for the admin subdomain
admin_subdomain_patterns = admin_subdomain_base
# admin_subdomain_patterns = admin_subdomain_base + admin_crud_patterns  # TODO: Re-enable once all view functions are implemented

# Main urlpatterns - exclude admin_crud_patterns as most view functions are not yet implemented
urlpatterns = admin_patterns + seller_patterns + deployment_patterns
