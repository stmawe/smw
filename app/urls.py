from django.urls import path
from . import views


urlpatterns = [
    path('', views.refs, name='index'),
    #path('track/', views.track, name='track'),
    #path('login/', views.login, name='login'),
    #path('register_vehicle/', views.register_vehicle, name='register_vehicle'),
    path('h/', views.homepage_view, name='homepage'),
    path('about/', views.about_view, name='about'),
    path('features/', views.features_view, name='features'),
    path('blog/', views.blog_view, name='blog'),
    path('faq/', views.faq_view, name='faq'),
    path('contact/', views.contact_view, name='contact'),
    path('products/', views.products_view, name='products'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
]