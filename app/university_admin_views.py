"""University admin views and dashboard."""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.db.models import Count, Sum, Q, Avg
from app.models import Client
from mydak.models import Shop, Listing, Transaction

logger = logging.getLogger(__name__)


def university_admin_required(view_func):
    """Decorator to check if user is a university admin."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if request.user.role != 'university_admin':
            django_messages.error(request, 'You do not have permission to access this area')
            return redirect('/')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


@login_required
@university_admin_required
@require_http_methods(['GET'])
def university_dashboard_view(request):
    """University admin main dashboard."""
    try:
        # Get university tenant
        university = Client.objects.filter(
            owner=request.user,
            tenant_type='university'
        ).first()
        
        if not university:
            django_messages.error(request, 'No university found for your account')
            return redirect('/')
        
        # Get stats
        shops = Shop.objects.filter(owner__in=university.get_users())
        listings = Listing.objects.filter(shop__in=shops)
        transactions = Transaction.objects.filter(user__in=university.get_users())
        
        total_shops = shops.count()
        active_listings = listings.filter(status='active').count()
        total_revenue = sum(t.amount for t in transactions.filter(status='success'))
        suspended_shops = shops.filter(is_active=False).count()
        
        context = {
            'university': university,
            'total_shops': total_shops,
            'active_listings': active_listings,
            'total_revenue': total_revenue,
            'suspended_shops': suspended_shops,
            'shops': shops[:10],
            'recent_transactions': transactions.filter(status='success')[:5],
        }
        
        return render(request, 'admin/university_dashboard.html', context)
    
    except Exception as e:
        logger.error(f'Error loading university dashboard: {e}')
        django_messages.error(request, 'Error loading dashboard')
        return redirect('/')


@login_required
@university_admin_required
@require_http_methods(['GET', 'POST'])
def university_shops_view(request):
    """View and manage shops within university."""
    try:
        university = Client.objects.filter(
            owner=request.user,
            tenant_type='university'
        ).first()
        
        if not university:
            return redirect('/')
        
        shops = Shop.objects.filter(owner__in=university.get_users())
        
        if request.method == 'POST':
            action = request.POST.get('action')
            shop_id = request.POST.get('shop_id')
            shop = get_object_or_404(shops, id=shop_id)
            
            if action == 'suspend':
                shop.deactivate()
                django_messages.success(request, f'Shop {shop.name} suspended')
            elif action == 'reinstate':
                shop.activate()
                django_messages.success(request, f'Shop {shop.name} reinstated')
            
            return redirect('university_shops')
        
        context = {
            'university': university,
            'shops': shops,
            'total': shops.count(),
            'active': shops.filter(is_active=True).count(),
            'suspended': shops.filter(is_active=False).count(),
        }
        
        return render(request, 'admin/university_shops.html', context)
    
    except Exception as e:
        logger.error(f'Error in university_shops_view: {e}')
        django_messages.error(request, 'Error loading shops')
        return redirect('/')


@login_required
@university_admin_required
@require_http_methods(['GET'])
def university_listings_view(request):
    """View and moderate listings within university."""
    try:
        university = Client.objects.filter(
            owner=request.user,
            tenant_type='university'
        ).first()
        
        if not university:
            return redirect('/')
        
        shops = Shop.objects.filter(owner__in=university.get_users())
        listings = Listing.objects.filter(shop__in=shops).order_by('-created_at')
        
        # Filter by status
        status = request.GET.get('status')
        if status and status in ['active', 'sold', 'expired', 'draft', 'hidden']:
            listings = listings.filter(status=status)
        
        context = {
            'university': university,
            'listings': listings[:50],
            'total': listings.count(),
            'by_status': {
                'active': listings.filter(status='active').count(),
                'sold': listings.filter(status='sold').count(),
                'expired': listings.filter(status='expired').count(),
                'draft': listings.filter(status='draft').count(),
                'hidden': listings.filter(status='hidden').count(),
            }
        }
        
        return render(request, 'admin/university_listings.html', context)
    
    except Exception as e:
        logger.error(f'Error in university_listings_view: {e}')
        django_messages.error(request, 'Error loading listings')
        return redirect('/')


@login_required
@university_admin_required
@require_http_methods(['GET'])
def university_analytics_view(request):
    """View analytics for university marketplace."""
    try:
        university = Client.objects.filter(
            owner=request.user,
            tenant_type='university'
        ).first()
        
        if not university:
            return redirect('/')
        
        shops = Shop.objects.filter(owner__in=university.get_users())
        listings = Listing.objects.filter(shop__in=shops)
        transactions = Transaction.objects.filter(user__in=university.get_users())
        
        # Calculate metrics
        total_listings_posted = listings.count()
        total_listings_sold = listings.filter(status='sold').count()
        avg_listing_price = listings.aggregate(
            avg_price=models.Avg('price')
        )['avg_price'] or 0
        
        total_transactions = transactions.filter(status='success').count()
        total_revenue = sum(t.amount for t in transactions.filter(status='success'))
        
        # Top shops by sales
        from django.db.models import Count, Sum
        top_shops = Shop.objects.filter(
            owner__in=university.get_users()
        ).annotate(
            sold_count=Count('listings', filter=models.Q(listings__status='sold')),
            total_sales=Sum('transactions__amount', filter=models.Q(transactions__status='success'))
        ).order_by('-sold_count')[:10]
        
        context = {
            'university': university,
            'total_listings_posted': total_listings_posted,
            'total_listings_sold': total_listings_sold,
            'avg_listing_price': avg_listing_price,
            'total_transactions': total_transactions,
            'total_revenue': total_revenue,
            'top_shops': top_shops,
        }
        
        return render(request, 'admin/university_analytics.html', context)
    
    except Exception as e:
        logger.error(f'Error in university_analytics_view: {e}')
        django_messages.error(request, 'Error loading analytics')
        return redirect('/')
