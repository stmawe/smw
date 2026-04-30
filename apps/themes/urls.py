"""URL routes for themes app."""

from django.urls import path
from . import views

app_name = 'themes'

urlpatterns = [
    # List and browse themes
    path('', views.theme_list_view, name='list'),
    
    # Apply theme to shop
    path('apply/<int:theme_id>/', views.theme_apply_view, name='apply'),
    
    # Customize theme
    path('customize/<int:shop_id>/', views.theme_customize_view, name='customize'),
    
    # Preview theme
    path('preview/<int:theme_id>/', views.theme_preview_view, name='preview'),
    
    # Get theme CSS
    path('css/', views.theme_css_view, name='css'),
    path('css/<int:shop_id>/', views.theme_css_view, name='css_shop'),
]
