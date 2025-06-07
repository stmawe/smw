from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

# Import the new and existing views
from .views import (
    BlogListView,
    BlogDetailView,
    tenant_register_view,  # <-- Import the new registration view
    login_view
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

    # --- AUTH URLS ---
    path('login/', login_view, name='login'),  # Keep your login view
    # Point 'register/' to the new tenant registration logic
    path('register/', tenant_register_view, name='register'),

    # --- BLOG URLS ---
    path('blog/', BlogListView.as_view(), name='blog'),
    path('blog/<slug:slug>/', BlogDetailView.as_view(), name='blog_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
