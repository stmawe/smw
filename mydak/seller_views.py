"""Seller dashboard views."""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.db.models import Count, Sum, Q, Avg
from mydak.models import Shop, Listing, Message, Conversation, Transaction

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(['GET'])
def seller_dashboard_view(request):
    """Seller main dashboard."""
    try:
        shops = Shop.objects.filter(owner=request.user)
        
        if not shops.exists():
            django_messages.info(request, 'Create a shop to get started')
            return redirect('shops:create')
        
        # Get selected shop (default to first)
        shop_id = request.GET.get('shop_id') or shops.first().id
        shop = get_object_or_404(shops, id=shop_id)
        
        # Get metrics
        listings = Listing.objects.filter(shop=shop)
        messages = Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user))
        transactions = Transaction.objects.filter(user=request.user)
        
        total_listings = listings.count()
        active_listings = listings.filter(status='active').count()
        sold_listings = listings.filter(status='sold').count()
        avg_price = listings.aggregate(avg=Avg('price'))['avg'] or 0
        total_views = listings.aggregate(total=Sum('views'))['total'] or 0
        unread_messages = messages.filter(receiver=request.user, is_read=False).count()
        
        revenue = sum(t.amount for t in transactions.filter(status='success', action='item_purchase'))
        pending_payments = sum(t.amount for t in transactions.filter(status='initiated'))
        
        context = {
            'shop': shop,
            'shops': shops,
            'total_listings': total_listings,
            'active_listings': active_listings,
            'sold_listings': sold_listings,
            'avg_price': avg_price,
            'total_views': total_views,
            'unread_messages': unread_messages,
            'revenue': revenue,
            'pending_payments': pending_payments,
            'recent_listings': listings.order_by('-created_at')[:5],
            'recent_messages': messages.order_by('-created_at')[:5],
        }
        
        return render(request, 'seller/dashboard.html', context)
    
    except Exception as e:
        logger.error(f'Error loading seller dashboard: {e}')
        django_messages.error(request, 'Error loading dashboard')
        return redirect('/')


@login_required
@require_http_methods(['GET'])
def seller_listings_view(request):
    """View seller's listings with stats."""
    try:
        shops = Shop.objects.filter(owner=request.user)
        shop_id = request.GET.get('shop_id') or shops.first().id
        shop = get_object_or_404(shops, id=shop_id)
        
        listings = Listing.objects.filter(shop=shop)
        
        # Filter by status
        status = request.GET.get('status')
        if status and status in ['active', 'sold', 'expired', 'draft', 'hidden']:
            listings = listings.filter(status=status)
        
        context = {
            'shop': shop,
            'shops': shops,
            'listings': listings.order_by('-created_at'),
            'stats': {
                'total': Listing.objects.filter(shop=shop).count(),
                'active': Listing.objects.filter(shop=shop, status='active').count(),
                'sold': Listing.objects.filter(shop=shop, status='sold').count(),
                'draft': Listing.objects.filter(shop=shop, status='draft').count(),
                'total_views': Listing.objects.filter(shop=shop).aggregate(Sum('views'))['views__sum'] or 0,
            }
        }
        
        return render(request, 'seller/listings.html', context)
    
    except Exception as e:
        logger.error(f'Error in seller_listings_view: {e}')
        django_messages.error(request, 'Error loading listings')
        return redirect('/')


@login_required
@require_http_methods(['GET'])
def seller_messages_view(request):
    """View seller conversations and messages."""
    try:
        conversations = Conversation.objects.filter(
            Q(seller=request.user) | Q(buyer=request.user)
        ).order_by('-last_message_at')
        
        # Filter by shop
        shop_id = request.GET.get('shop_id')
        if shop_id:
            conversations = conversations.filter(listing__shop_id=shop_id)
        
        # Get selected conversation
        conversation_id = request.GET.get('conversation_id')
        selected_conversation = None
        if conversation_id:
            selected_conversation = get_object_or_404(conversations, id=conversation_id)
            messages = selected_conversation.messages.all()
        else:
            messages = []
        
        context = {
            'conversations': conversations[:20],
            'selected_conversation': selected_conversation,
            'messages': messages,
            'total_unread': sum(
                c.messages.filter(receiver=request.user, is_read=False).count() 
                for c in conversations
            ),
        }
        
        return render(request, 'seller/messages.html', context)
    
    except Exception as e:
        logger.error(f'Error in seller_messages_view: {e}')
        django_messages.error(request, 'Error loading messages')
        return redirect('/')


@login_required
@require_http_methods(['GET'])
def seller_analytics_view(request):
    """View seller analytics and statistics."""
    try:
        shops = Shop.objects.filter(owner=request.user)
        shop_id = request.GET.get('shop_id') or shops.first().id
        shop = get_object_or_404(shops, id=shop_id)
        
        listings = Listing.objects.filter(shop=shop)
        
        # Calculate metrics
        total_listed = listings.count()
        total_sold = listings.filter(status='sold').count()
        total_views = listings.aggregate(total=Sum('views'))['total'] or 0
        avg_price = listings.aggregate(avg=Avg('price'))['avg'] or 0
        
        # Views per listing
        views_per_listing = total_views / total_listed if total_listed > 0 else 0
        
        # Conversion rate (sold / views)
        conversion_rate = (total_sold / total_views * 100) if total_views > 0 else 0
        
        # Revenue
        transactions = Transaction.objects.filter(
            user=request.user,
            status='success'
        )
        total_revenue = sum(t.amount for t in transactions)
        
        context = {
            'shop': shop,
            'shops': shops,
            'total_listed': total_listed,
            'total_sold': total_sold,
            'total_views': total_views,
            'avg_price': avg_price,
            'views_per_listing': round(views_per_listing, 2),
            'conversion_rate': round(conversion_rate, 2),
            'total_revenue': total_revenue,
            'featured_listings': listings.filter(is_featured=True).count(),
            'active_listings': listings.filter(status='active').count(),
            'top_listings_by_views': listings.order_by('-views')[:5],
        }
        
        return render(request, 'seller/analytics.html', context)
    
    except Exception as e:
        logger.error(f'Error in seller_analytics_view: {e}')
        django_messages.error(request, 'Error loading analytics')
        return redirect('/')


@login_required
@require_http_methods(['GET', 'POST'])
def seller_settings_view(request):
    """Seller account and shop settings."""
    try:
        shops = Shop.objects.filter(owner=request.user)
        shop_id = request.GET.get('shop_id') or shops.first().id
        shop = get_object_or_404(shops, id=shop_id)
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'update_theme':
                theme_id = request.POST.get('theme_id')
                shop.theme_id = theme_id
                shop.save()
                django_messages.success(request, 'Theme updated')
            
            elif action == 'update_profile':
                shop.description = request.POST.get('description', '')
                if 'logo' in request.FILES:
                    shop.logo = request.FILES['logo']
                shop.save()
                django_messages.success(request, 'Shop profile updated')
            
            return redirect('seller_settings')
        
        context = {
            'shop': shop,
            'shops': shops,
        }
        
        return render(request, 'seller/settings.html', context)
    
    except Exception as e:
        logger.error(f'Error in seller_settings_view: {e}')
        django_messages.error(request, 'Error updating settings')
        return redirect('/')


@login_required
@require_http_methods(['GET'])
def seller_insights_view(request):
    """Advanced analytics and insights for sellers."""
    from mydak.analytics import SellerAnalytics
    
    try:
        shops = Shop.objects.filter(owner=request.user)
        
        if not shops.exists():
            django_messages.info(request, 'Create a shop to get analytics')
            return redirect('shops:create')
        
        # Get selected shop
        shop_id = request.GET.get('shop_id') or shops.first().id
        shop = get_object_or_404(shops, id=shop_id)
        
        # Get various analytics
        daily_sales = SellerAnalytics.get_daily_sales(shop, days=30)
        conversion_funnel = SellerAnalytics.get_conversion_funnel(shop)
        top_keywords = SellerAnalytics.get_top_keywords(shop, limit=10)
        performance_summary = SellerAnalytics.get_performance_summary(shop)
        top_listings = SellerAnalytics.get_top_listings(shop, limit=5)
        category_performance = SellerAnalytics.get_category_performance(shop)
        
        context = {
            'shop': shop,
            'shops': shops,
            'daily_sales': daily_sales,
            'conversion_funnel': conversion_funnel,
            'top_keywords': top_keywords,
            'performance_summary': performance_summary,
            'top_listings': top_listings,
            'category_performance': category_performance,
        }
        
        return render(request, 'seller/insights.html', context)
    
    except Exception as e:
        logger.error(f'Error in seller_insights_view: {e}')
        django_messages.error(request, 'Error loading insights')
        return redirect('seller_dashboard')
