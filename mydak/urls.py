"""URLs for shop and listing management."""

from django.urls import path
from . import views
from . import listing_views
from . import payment_views
from . import bulk_listing_views
from . import template_views

app_name = 'shops'

urlpatterns = [
    # Shop creation and management
    path('create/', views.shop_create_view, name='create'),
    path('list/', views.shop_list_view, name='list'),
    path('<int:shop_id>/', views.shop_detail_view, name='detail'),
    path('<int:shop_id>/edit/', views.shop_edit_view, name='edit'),
    path('<int:shop_id>/deactivate/', views.shop_deactivate_view, name='deactivate'),
    path('<int:shop_id>/reactivate/', views.shop_reactivate_view, name='reactivate'),
]

# Listing URLs
listing_patterns = [
    path('search/', listing_views.listing_search_view, name='search'),
    path('my/', listing_views.my_listings_view, name='my_listings'),
    path('<int:listing_id>/', listing_views.listing_detail_view, name='detail'),
    path('<int:listing_id>/edit/', listing_views.listing_edit_view, name='edit'),
    path('<int:listing_id>/delete/', listing_views.listing_delete_view, name='delete'),
    path('<int:listing_id>/publish/', listing_views.listing_publish_view, name='publish'),
    path('<int:listing_id>/sold/', listing_views.listing_mark_sold_view, name='mark_sold'),
    path('shop/<int:shop_id>/create/', listing_views.listing_create_view, name='create'),
    path('bulk/upload/', bulk_listing_views.bulk_listing_upload_view, name='bulk_upload'),
    path('bulk/preview/', bulk_listing_views.bulk_listing_preview_view, name='bulk_preview'),
    path('bulk/confirm/', bulk_listing_views.bulk_listing_confirm_view, name='bulk_confirm'),
    path('bulk/cancel/', bulk_listing_views.bulk_listing_cancel_view, name='bulk_cancel'),
    path('template/create/', template_views.template_create_view, name='template_create'),
    path('template/list/', template_views.template_list_view, name='template_list'),
    path('template/<int:template_id>/edit/', template_views.template_edit_view, name='template_edit'),
    path('template/<int:template_id>/delete/', template_views.template_delete_view, name='template_delete'),
    path('template/<int:template_id>/create-listing/', template_views.create_listing_from_template_view, name='create_from_template'),
    path('<int:listing_id>/clone-as-template/', template_views.clone_listing_as_template_view, name='clone_as_template'),
]

# Payment URLs
payment_patterns = [
    path('payment/<int:transaction_id>/initiate/', payment_views.payment_initiate_view, name='payment_initiate'),
    path('payment/<int:transaction_id>/status/', payment_views.payment_status_view, name='payment_status'),
    path('payment/action/<str:action>/', payment_views.payment_action_view, name='payment_action'),
    path('api/mpesa/callback/', payment_views.mpesa_callback_view, name='mpesa_callback'),
    path('api/mpesa/timeout/', payment_views.mpesa_timeout_view, name='mpesa_timeout'),
]

urlpatterns.extend(listing_patterns)
urlpatterns.extend(payment_patterns)
