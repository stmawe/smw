from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now

User = get_user_model()


class Shop(models.Model):
    """
    Represents a customizable shop within a tenant's schema.
    Includes support for subdomain routing, activation status, and analytics.
    """
    name = models.CharField(max_length=255)  # Name of the shop
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shops'
    )  # Owner of the shop (user reference)
    template = models.CharField(
        max_length=255,
        default='default'
    )  # Dynamic shop templates (e.g., 'modern', 'classic')
    domain = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )  # Subdomain for the shop (e.g., shopname.university.domain.tld)
    is_active = models.BooleanField(default=False)  # Activated after payment
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for creation
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp for last update

    def __str__(self):
        return self.name

    @property
    def full_domain(self):
        """
        Returns the full domain for the shop.
        Example: shopname.university.domain.tld
        """
        if self.domain:
            return f"{self.domain}.domain.tld"
        return None

    def activate(self):
        """
        Activates the shop after payment confirmation.
        """
        self.is_active = True
        self.save()

    def deactivate(self):
        """
        Deactivates the shop (e.g., due to non-payment).
        """
        self.is_active = False
        self.save()


class Listing(models.Model):
    """
    Represents an item listing within a tenant's schema.
    Listings belong to a specific tenant (University or Area).
    """
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name='listings', null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey('app.Category', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Transaction(models.Model):
    """
    Tracks financial transactions related to shops (e.g., shop creation fees, ad purchases).
    """
    TRANSACTION_TYPES = (
        ('shop_creation', 'Shop Creation Fee'),
        ('ad_purchase', 'Ad Purchase'),
        ('item_purchase', 'Item Purchase'),
    )

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True
    )  # Associated shop (if applicable)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )  # User who initiated the transaction
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Transaction amount
    type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)  # Type of transaction
    status = models.CharField(
        max_length=20,
        default='pending',
        choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')]
    )  # Status of the transaction
    timestamp = models.DateTimeField(auto_now_add=True)  # Timestamp for the transaction
    reference_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )  # Reference ID from payment gateway (e.g., M-Pesa or Stripe)

    def __str__(self):
        return f"{self.type} - {self.amount} ({self.status})"


class Message(models.Model):
    """
    Stores messages for buyer-seller communication within a tenant's schema.
    """
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    listing = models.ForeignKey('Listing', on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}"


class ShopAnalytics(models.Model):
    """
    Stores analytics data for shops, including sales, visits, and listings.
    """
    shop = models.OneToOneField(
        Shop,
        on_delete=models.CASCADE,
        related_name='analytics'
    )  # Associated shop
    total_listings = models.PositiveIntegerField(default=0)  # Total number of listings
    total_sales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )  # Total revenue from item sales
    total_visits = models.PositiveIntegerField(default=0)  # Total visits to the shop
    last_updated = models.DateTimeField(default=now)  # Timestamp for last update

    def __str__(self):
        return f"Analytics for {self.shop.name}"
    
    

class Payment(models.Model):
   
    PAYMENT_METHODS = (
        ('mpesa', 'M-Pesa'),
        ('stripe', 'Stripe'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, default='pending', choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method} - {self.amount} ({self.status})"