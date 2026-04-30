"""URL routes for accounts."""

from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    # Allauth URLs (includes account login, logout, email confirmation, password reset, social auth)
    path('auth/', include('allauth.urls')),
    
    # Custom auth views
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('verify-email/<str:key>/', views.verify_email_view, name='verify_email'),
]
