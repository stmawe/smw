"""Seller analytics and insights."""

from django.db.models import Count, Sum, Q, F, Avg
from django.utils import timezone
from datetime import timedelta
from mydak.models import Listing, Transaction, Message, Shop


class SellerAnalytics:
    """Calculate advanced seller analytics."""
    
    @staticmethod
    def get_hourly_sales(shop, days=7):
        """Get hourly sales data for the past N days."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        transactions = Transaction.objects.filter(
            shop=shop,
            status='success',
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('user')
        
        # Group by hour
        hourly_data = {}
        for hour in range(days * 24):
            hour_start = start_date + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            
            count = transactions.filter(
                created_at__gte=hour_start,
                created_at__lt=hour_end
            ).count()
            
            hourly_data[hour_start.isoformat()] = count
        
        return hourly_data
    
    @staticmethod
    def get_daily_sales(shop, days=30):
        """Get daily sales data."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        transactions = Transaction.objects.filter(
            shop=shop,
            status='success',
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        daily_data = {}
        for day in range(days):
            day_start = start_date + timedelta(days=day)
            day_end = day_start + timedelta(days=1)
            
            amount = transactions.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            daily_data[day_start.date().isoformat()] = float(amount)
        
        return daily_data
    
    @staticmethod
    def get_conversion_funnel(shop):
        """Get buyer funnel: views → messages → transactions."""
        
        listings = Listing.objects.filter(shop=shop, status='active')
        
        total_views = sum(l.view_count for l in listings)
        
        # Listings that have messages
        listings_with_messages = listings.annotate(
            message_count=Count('message')
        ).filter(message_count__gt=0).count()
        
        # Listings with successful sales
        listings_sold = Listing.objects.filter(
            shop=shop,
            status='sold'
        ).count()
        
        return {
            'total_views': total_views,
            'listings_with_interest': listings_with_messages,
            'listings_sold': listings_sold,
            'conversion_rate': (
                (listings_sold / listings.count() * 100)
                if listings.count() > 0
                else 0
            ),
        }
    
    @staticmethod
    def get_top_keywords(shop, limit=10):
        """Get top searched keywords leading to shop listings."""
        
        listings = Listing.objects.filter(shop=shop).values('title')
        
        # Extract keywords from titles
        keyword_freq = {}
        for listing in listings:
            title = listing['title'].lower()
            words = title.split()
            
            # Filter out common words
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were'}
            for word in words:
                word = word.strip('.,!?;:')
                if word not in stopwords and len(word) > 3:
                    keyword_freq[word] = keyword_freq.get(word, 0) + 1
        
        # Sort and return top keywords
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        return dict(top_keywords[:limit])
    
    @staticmethod
    def get_performance_summary(shop):
        """Get overall performance summary."""
        
        listings = Listing.objects.filter(shop=shop)
        active_listings = listings.filter(status='active').count()
        sold_listings = listings.filter(status='sold').count()
        
        transactions = Transaction.objects.filter(shop=shop, status='success')
        total_revenue = transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        messages = Message.objects.filter(
            conversation__seller=shop.owner
        ).count()
        
        avg_response_time = None  # Would require tracking first message time
        
        return {
            'active_listings': active_listings,
            'total_listings': listings.count(),
            'sold_listings': sold_listings,
            'total_revenue': float(total_revenue),
            'message_count': messages,
            'avg_response_time': avg_response_time,
        }
    
    @staticmethod
    def get_top_listings(shop, limit=5):
        """Get top performing listings by views and sales."""
        
        listings = Listing.objects.filter(shop=shop).annotate(
            message_count=Count('message')
        ).order_by('-view_count')[:limit]
        
        return [
            {
                'id': listing.id,
                'title': listing.title,
                'price': float(listing.price),
                'views': listing.view_count,
                'interest_count': listing.message_count,
                'status': listing.status,
            }
            for listing in listings
        ]
    
    @staticmethod
    def get_category_performance(shop):
        """Get performance by category."""
        
        categories = Listing.objects.filter(
            shop=shop
        ).values('category__name').annotate(
            count=Count('id'),
            views=Sum('view_count'),
            sold=Count('id', filter=Q(status='sold'))
        ).order_by('-views')
        
        return list(categories)
