from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from accounts.views import login_view as accounts_login_view

# Import the new and existing views
from .views import (
    BlogListView,
    BlogDetailView,
    tenant_register_view,
    explore_view,
    listings_view,
    shop_detail_view,
    listing_detail_view,
    universities_view,
    locations_view,
    create_shop_view
)

# Import shop endpoints
from .shop_endpoints import (
    shop_url_api,
    shop_sharing_page,
    validate_shop_slug_api
)
from .shop_launch_views import (
    create_shop_api_view,
    shop_email_verification_send_view,
    shop_email_verification_verify_view,
    shop_mpesa_callback_view,
    shop_payment_status_api,
)

urlpatterns = [
    path('', views.refs, name='index'),
    path('search/', views.search, name='search'),
    path('h/', views.homepage_view, name='homepage'),
    path('index2/', views.homepage_view_x, name='indexx'),
    path('about/', views.about_view, name='about'),
    path('features/', views.features_view, name='features'),
    path('faq/', views.faq_view, name='faq'),
    path('contact/', views.contact_view, name='contact'),
    path('products/', views.products_view, name='products'),

    # --- MARKETPLACE URLS ---
    path('explore/', explore_view, name='explore'),
    path('listings/', listings_view, name='listings'),
    path('shop/<int:shop_id>/', shop_detail_view, name='shop_detail'),
    path('listing/<int:listing_id>/', listing_detail_view, name='listing_detail'),
    path('universities/', universities_view, name='universities'),
    path('locations/', locations_view, name='locations'),
    path('create-shop/', create_shop_view, name='create_shop'),

    # --- AUTH URLS ---
    path('login/', accounts_login_view, name='login'),  # Use accounts login which works
    # Point 'register/' to the new tenant registration logic
    path('register/', tenant_register_view, name='register'),

    # --- BLOG URLS ---
    path('blog/', BlogListView.as_view(), name='blog'),
    path('blog/<slug:slug>/', BlogDetailView.as_view(), name='blog_detail'),
    
    # --- SHOP URL & SHARING ENDPOINTS ---
    path('api/shop/<int:shop_id>/url/', shop_url_api, name='shop_url_api'),
    path('shop/<int:shop_id>/share/', shop_sharing_page, name='shop_sharing'),
    path('api/check-slug/', validate_shop_slug_api, name='check_slug_api'),
    path('api/create-shop/', create_shop_api_view, name='create_shop_api'),
    path('api/email-verification/send/', shop_email_verification_send_view, name='shop_email_verification_send'),
    path('api/email-verification/verify/', shop_email_verification_verify_view, name='shop_email_verification_verify'),
    path('api/mpesa-callback/', shop_mpesa_callback_view, name='shop_mpesa_callback'),
    path('api/poll-payment/', shop_payment_status_api, name='shop_payment_status'),
    path('api/validate-slug/', validate_shop_slug_api, name='validate_slug_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
