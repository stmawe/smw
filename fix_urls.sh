#!/bin/bash
cd /usr/home/wiptech/domains/smw.pgwiz.cloud/public_python

# Simple Python script to fix URLs and admin_urls
python3 << 'EOFPYTHON'
# Fix urls.py - ensure admin_subdomain_patterns is included
urls_content = '''from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app.admin_urls import admin_subdomain_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('themes/', include('apps.themes.urls')),
    path('shops/', include('mydak.urls')),
    path('dashboard/', include('app.admin_urls')),
    path('', include(admin_subdomain_patterns)),
    path('', include('app.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
'''

with open('smw/urls.py', 'w') as f:
    f.write(urls_content)

# Fix admin_urls.py - add admin_subdomain_patterns
admin_urls_content = '''from django.urls import path
from . import university_admin_views, deployment_views, admin_views, admin_console_views
from mydak import seller_views

admin_subdomain_patterns = [
    path('', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard_full'),
    path('<str:username>/', admin_views.admin_dashboard_view, name='admin_dashboard_user'),
    path('<str:username>/dashboard/', admin_views.admin_dashboard_view, name='admin_dashboard_user_full'),
    path('<str:username>/shops/', admin_views.admin_shops_view, name='admin_shops'),
    path('<str:username>/shop/<int:shop_id>/', admin_views.admin_shop_detail_view, name='admin_shop_detail'),
    path('console/domains/', admin_console_views.domains_console_view, name='admin_console_domains'),
    path('console/domains/<int:shop_id>/ssl/', admin_console_views.add_ssl_for_shop_view, name='admin_add_ssl'),
    path('console/domains/<int:shop_id>/status/', admin_console_views.ssl_status_view, name='admin_ssl_status'),
]

admin_patterns = [
    path('university/dashboard/', university_admin_views.university_dashboard_view, name='university_dashboard'),
    path('university/shops/', university_admin_views.university_shops_view, name='university_shops'),
    path('university/listings/', university_admin_views.university_listings_view, name='university_listings'),
    path('university/analytics/', university_admin_views.university_analytics_view, name='university_analytics'),
]

seller_patterns = [
    path('seller/dashboard/', seller_views.seller_dashboard_view, name='seller_dashboard'),
    path('seller/listings/', seller_views.seller_listings_view, name='seller_listings'),
    path('seller/messages/', seller_views.seller_messages_view, name='seller_messages'),
    path('seller/analytics/', seller_views.seller_analytics_view, name='seller_analytics'),
    path('seller/insights/', seller_views.seller_insights_view, name='seller_insights'),
    path('seller/settings/', seller_views.seller_settings_view, name='seller_settings'),
]

deployment_patterns = [
    path('deployment/dashboard/', deployment_views.deployment_dashboard_view, name='deployment_dashboard'),
    path('deployment/update/', deployment_views.trigger_site_update_view, name='trigger_site_update'),
    path('deployment/logs/', deployment_views.get_deployment_logs_view, name='get_deployment_logs'),
]

urlpatterns = admin_patterns + seller_patterns + deployment_patterns
'''

with open('app/admin_urls.py', 'w') as f:
    f.write(admin_urls_content)

print('Fixed urls.py and admin_urls.py')
EOFPYTHON

devil www restart smw.pgwiz.cloud
sleep 2
curl -I https://admin.smw.pgwiz.cloud/console/domains/ 2>/dev/null
