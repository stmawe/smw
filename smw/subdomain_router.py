"""
Custom subdomain routing for SMW marketplace.
Handles routing of shop subdomains and admin subdomains.
"""

from django.urls import path, include, re_path
from django.http import HttpResponse

def get_urls_for_subdomain(subdomain, path):
    """
    Determine the correct URL configuration based on subdomain.
    
    Rules:
    - admin.smw.pgwiz.cloud -> admin dashboard routes
    - username.smw.pgwiz.cloud -> shop routes
    - www.smw.pgwiz.cloud or smw.pgwiz.cloud -> main public routes
    """
    from app import views as app_views
    from app import admin_urls
    from accounts import views as account_views
    from mydak import views as shop_views
    
    # Admin subdomain
    if subdomain == 'admin':
        return [
            path('', admin_urls.admin_dashboard_view, name='admin_dashboard'),
            path('<str:username>/dashboard/', admin_urls.admin_dashboard_view, name='admin_dashboard_user'),
            path('<str:username>/shops/', admin_urls.admin_shops_view, name='admin_shops'),
            path('<str:username>/shop/<int:shop_id>/', admin_urls.admin_shop_detail_view, name='admin_shop_detail'),
        ]
    
    # Shop subdomains (username or shop-name based)
    elif subdomain and subdomain not in ['www', 'mail', 'ftp']:
        # This is a shop subdomain
        return [
            path('', shop_views.shop_subdomain_view, name='shop_subdomain'),
            path('products/', shop_views.shop_products_view, name='shop_products'),
            path('product/<int:product_id>/', shop_views.shop_product_detail_view, name='shop_product_detail'),
            path('about/', shop_views.shop_about_view, name='shop_about'),
        ]
    
    # Default/public site URLs
    else:
        from app import urls as app_urls
        return app_urls.urlpatterns
