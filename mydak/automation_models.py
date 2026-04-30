"""Seller automation rules and tasks."""

from django.db import models
from apps.core.models import TimeStampedModel
from django.contrib.auth import get_user_model
from mydak.models import Shop, Listing

User = get_user_model()


class SellerRule(TimeStampedModel):
    """Automation rules for sellers."""
    
    RULE_TYPES = [
        ('auto_relist', 'Auto-relist Expired'),
        ('price_adjust', 'Adjust Price'),
        ('auto_decline', 'Auto-decline Low Offers'),
        ('auto_feature', 'Auto-feature Listings'),
        ('auto_republish', 'Auto-republish Old Listings'),
    ]
    
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='seller_rules'
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='automation_rules'
    )
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Rule conditions
    is_active = models.BooleanField(default=True, db_index=True)
    condition_min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    condition_max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    condition_category = models.ForeignKey(
        'mydak.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Rule actions
    action_param_1 = models.CharField(max_length=255, blank=True, help_text='Param 1 (e.g., percent for price adjust)')
    action_param_2 = models.CharField(max_length=255, blank=True, help_text='Param 2')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'shop', 'is_active']),
            models.Index(fields=['rule_type']),
        ]
    
    def __str__(self):
        return f'{self.name} ({self.get_rule_type_display()})'
    
    def apply(self, listing):
        """Apply this rule to a listing."""
        if self.rule_type == 'auto_relist' and listing.status == 'expired':
            listing.mark_as_active()
            return True
        
        elif self.rule_type == 'price_adjust':
            try:
                percent_change = float(self.action_param_1)
                new_price = listing.price * (1 + percent_change / 100)
                listing.price = new_price
                listing.save()
                return True
            except (ValueError, TypeError):
                return False
        
        return False


class AutomationLog(TimeStampedModel):
    """Log of automation rule executions."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    rule = models.ForeignKey(
        SellerRule,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='automation_logs'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rule', 'status']),
        ]
    
    def __str__(self):
        return f'{self.rule.name} on {self.listing.title} - {self.get_status_display()}'


class OfferRule(TimeStampedModel):
    """Rules for handling offers and negotiations."""
    
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='offer_rules'
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='offer_rules'
    )
    
    # Offer thresholds
    min_acceptable_price_percent = models.IntegerField(
        default=80,
        help_text='Minimum price as % of listing price (e.g., 80 = reject below 80%)'
    )
    auto_decline_below_percent = models.BooleanField(default=False)
    auto_counter_offer = models.BooleanField(default=False)
    counter_offer_percent = models.IntegerField(
        default=10,
        help_text='Counter-offer increase as % (e.g., 10 = add 10% to their offer)'
    )
    
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        unique_together = [['shop', 'seller']]
    
    def should_decline_offer(self, listing_price, offer_price):
        """Check if offer should be auto-declined."""
        if not self.auto_decline_below_percent:
            return False
        
        offer_percent = (offer_price / listing_price) * 100
        return offer_percent < self.min_acceptable_price_percent
    
    def get_counter_offer(self, offer_price):
        """Calculate counter-offer price."""
        if not self.auto_counter_offer:
            return None
        
        return offer_price * (1 + self.counter_offer_percent / 100)
