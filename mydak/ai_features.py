"""AI and ML features for UniMarket (Bootstrap Implementation)."""

import logging
from django.db.models import Q, Count, Avg
from django.utils.timezone import now
from datetime import timedelta
from mydak.models import Listing, Conversation, Message, Transaction

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Bootstrap recommendation engine using simple heuristics."""
    
    @staticmethod
    def get_trending_listings(limit=10):
        """Get trending listings based on views and recency."""
        # Score: recent views + popularity
        from django.db.models import F
        from django.utils.timezone import now
        
        listings = Listing.objects.filter(
            status='active'
        ).annotate(
            # Listings posted in last 7 days get boost
            recency_score=Case(
                When(created_at__gte=now() - timedelta(days=7), then=Value(10)),
                When(created_at__gte=now() - timedelta(days=14), then=Value(5)),
                default=Value(1),
                output_field=models.IntegerField(),
            ),
            # Views count
            popularity_score=F('views')
        ).order_by('-popularity_score', '-created_at')[:limit]
        
        return listings
    
    @staticmethod
    def get_personalized_recommendations(user, limit=10):
        """Get personalized recommendations based on user history."""
        # Find user's viewing/purchase patterns
        viewed_listings = Conversation.objects.filter(
            Q(seller=user) | Q(buyer=user)
        ).values_list('listing__category', flat=True).distinct()
        
        if not viewed_listings:
            # Fallback to trending
            return RecommendationEngine.get_trending_listings(limit)
        
        # Recommend similar listings
        recommendations = Listing.objects.filter(
            status='active',
            category__in=viewed_listings
        ).exclude(
            seller=user
        ).annotate(
            score=Count('conversations')
        ).order_by('-score', '-created_at')[:limit]
        
        return recommendations
    
    @staticmethod
    def get_recommendations_for_buyer(user, limit=10):
        """Get recommendations tailored for a buyer."""
        # Get listings similar to ones they've inquired about
        inquired_listings = Conversation.objects.filter(
            buyer=user
        ).values_list('listing__category', flat=True).distinct()
        
        if not inquired_listings:
            return RecommendationEngine.get_trending_listings(limit)
        
        # Recommend listings in same categories with good reviews
        recommendations = Listing.objects.filter(
            status='active',
            category__in=inquired_listings
        ).exclude(
            seller=user
        ).annotate(
            engagement=Count('messages') + Count('views')
        ).order_by('-engagement', '-created_at')[:limit]
        
        return recommendations


class SearchRankingEngine:
    """Search ranking using heuristics (no ML needed for bootstrap)."""
    
    @staticmethod
    def rank_search_results(listings, query=None):
        """
        Rank listings by relevance and popularity.
        Factors: title match, recency, views, price competitiveness
        """
        from django.db.models import F, Case, When, Value, IntegerField
        
        # Start with all active listings
        ranked = listings.filter(status='active')
        
        # Add relevance score
        if query:
            # Exact title match gets high score
            ranked = ranked.annotate(
                relevance_score=Case(
                    When(title__iexact=query, then=Value(100)),
                    When(title__istartswith=query, then=Value(50)),
                    When(title__icontains=query, then=Value(25)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                # Recent listings get boost
                recency_boost=Case(
                    When(created_at__gte=now() - timedelta(days=7), then=Value(10)),
                    When(created_at__gte=now() - timedelta(days=14), then=Value(5)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                # Popular listings get boost
                popularity_boost=F('views') // 10,  # 1 point per 10 views
                
                # Featured listings get boost
                featured_boost=Case(
                    When(is_featured=True, then=Value(20)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                
                # Combined score
                search_score=F('relevance_score') + F('recency_boost') + 
                             F('popularity_boost') + F('featured_boost')
            ).order_by('-search_score', '-created_at')
        else:
            # No query - just use popularity and recency
            ranked = ranked.annotate(
                search_score=Case(
                    When(is_featured=True, then=Value(50)),
                    default=Value(0),
                    output_field=IntegerField(),
                ) + (F('views') // 10) + Case(
                    When(created_at__gte=now() - timedelta(days=7), then=Value(10)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).order_by('-search_score', '-created_at')
        
        return ranked


class FraudDetection:
    """Bootstrap fraud detection using simple rules."""
    
    @staticmethod
    def check_suspicious_activity(user):
        """Check for suspicious user activity."""
        alerts = []
        
        # Check for rapid listing creation
        recent_listings = Listing.objects.filter(
            seller=user,
            created_at__gte=now() - timedelta(hours=1)
        ).count()
        
        if recent_listings > 10:
            alerts.append({
                'type': 'rapid_listing_creation',
                'severity': 'medium',
                'message': f'{recent_listings} listings created in last hour'
            })
        
        # Check for rapid price changes
        recently_edited = Listing.objects.filter(
            seller=user,
            updated_at__gte=now() - timedelta(hours=24)
        ).count()
        
        if recently_edited > 20:
            alerts.append({
                'type': 'rapid_edits',
                'severity': 'low',
                'message': f'{recently_edited} listings edited in last 24 hours'
            })
        
        # Check transaction patterns
        suspicious_transactions = Transaction.objects.filter(
            user=user,
            created_at__gte=now() - timedelta(days=1)
        ).exclude(
            status='success'
        ).count()
        
        if suspicious_transactions > 5:
            alerts.append({
                'type': 'failed_transactions',
                'severity': 'medium',
                'message': f'{suspicious_transactions} failed transactions in 24 hours'
            })
        
        return alerts
    
    @staticmethod
    def check_suspicious_listing(listing):
        """Check if a listing seems suspicious."""
        issues = []
        
        # Check for extremely low prices (potential scam)
        similar = Listing.objects.filter(
            category=listing.category,
            status='active'
        ).exclude(id=listing.id).aggregate(Avg('price'))
        
        avg_price = similar.get('price__avg')
        if avg_price and listing.price < (avg_price * 0.2):
            issues.append('price_suspiciously_low')
        
        # Check for spam keywords
        spam_keywords = ['bitcoin', 'crypto', 'click here', 'free money', 'nigerian']
        listing_text = f"{listing.title} {listing.description}".lower()
        
        for keyword in spam_keywords:
            if keyword in listing_text:
                issues.append('spam_keyword_detected')
                break
        
        return issues


# Django models integration
from django.db import models
from django.db.models import Case, When, Value

# Register signals for automatic ranking updates
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Listing)
def update_listing_features(sender, instance, created, **kwargs):
    """Update listing features for ranking when listing is saved."""
    if created:
        logger.info(f'New listing created: {instance.id} - {instance.title}')
        
        # Check for fraud
        issues = FraudDetection.check_suspicious_listing(instance)
        if issues:
            logger.warning(f'Potential issues with listing {instance.id}: {issues}')
