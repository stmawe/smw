from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('', views.refs, name='index'),
    #path('track/', views.track, name='track'),
    #path('login/', views.login, name='login'),
    #path('register_vehicle/', views.register_vehicle, name='register_vehicle'),
    path('search/', views.search, name='search'),
    path('h/', views.homepage_view, name='homepage'),
    path('index2/', views.homepage_view_x, name='indexx'),
    path('about/', views.about_view, name='about'),
    path('features/', views.features_view, name='features'),
    path('blog/', views.blog_view, name='blog'),
    path('faq/', views.faq_view, name='faq'),
    path('contact/', views.contact_view, name='contact'),
    path('products/', views.products_view, name='products'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)