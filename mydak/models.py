from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.utils.text import slugify
from django.conf import settings
from apps.core.models import TimeStampedModel

User = get_user_model()


class Shop(TimeStampedModel):
    """
    Represents a customizable shop within a tenant's schema.
    Includes support for subdomain routing, activation status, and analytics.
    """
    name = models.CharField(max_length=255, db_index=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shops',
        db_index=True
    )
    theme_id = models.CharField(
        max_length=50,
        default='campus_light',
        help_text='Theme ID for the shop (e.g., dark_noir, campus_light)'
    )
    domain = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    description = models.TextField(blank=True, help_text='Shop description')
    logo = models.ImageField(upload_to='shop_logos/', null=True, blank=True)
    is_active = models.BooleanField(default=False, db_index=True)
    
    # SSL Certificate Fields
    has_ssl = models.BooleanField(default=False, help_text='Whether SSL certificate is active')
    ssl_subdomain = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text='Subdomain with SSL certificate (e.g., shop-name.smw.pgwiz.cloud)'
    )
    ssl_cert_path = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        help_text='Path to SSL certificate on server'
    )
    ssl_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='SSL certificate expiration date'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'is_active']),
            models.Index(fields=['theme_id']),
        ]

    def __str__(self):
        return self.name

    @property
    def full_domain(self):
        """
        Returns the full domain for the shop.
        """
        if self.domain:
            base_domain = settings.BASE_DOMAIN
            return f"{self.domain}.{base_domain}"
        return None

    def activate(self):
        """Activates the shop after payment confirmation."""
        self.is_active = True
        self.save()

    def deactivate(self):
        """Deactivates the shop (e.g., due to non-payment)."""
        self.is_active = False
        self.save()


class Category(TimeStampedModel):
    """Product category for marketplace organization."""
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='package', help_text='Icon name (e.g., package, book, laptop)')
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Listing(TimeStampedModel):
    """
    Represents an item listing within a tenant's schema.
    Listings belong to a specific tenant (University or Area).
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('expired', 'Expired'),
        ('draft', 'Draft'),
        ('hidden', 'Hidden'),
    ]
    
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='listings',
        db_index=True
    )
    shop = models.ForeignKey(
        'Shop',
        on_delete=models.CASCADE,
        related_name='listings',
        null=True,
        blank=True,
        db_index=True
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        db_index=True
    )
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='good'
    )
    image = models.ImageField(upload_to='listings/%Y/%m/', null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    views = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['is_featured', 'status']),
        ]

    def __str__(self):
        return self.title

    def mark_as_sold(self):
        """Mark listing as sold."""
        self.status = 'sold'
        self.save()


class Transaction(TimeStampedModel):
    """
    Tracks financial transactions related to shops and listings.
    Supports M-Pesa STK push flow and other payment methods.
    """
    ACTION_CHOICES = [
        ('shop_creation', 'Shop Creation Fee'),
        ('shop_premium', 'Premium Shop Template'),
        ('listing_post', 'Post a Listing'),
        ('listing_feature', 'Feature a Listing'),
        ('item_purchase', 'Item Purchase'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('initiated', 'Initiated (STK Sent)'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('expired', 'Expired'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Debit/Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        db_index=True
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True,
        db_index=True
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        db_index=True
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        db_index=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='mpesa'
    )
    phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text='Phone number for M-Pesa transactions (254XXXXXXXXX)'
    )
    reference_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    mpesa_receipt = models.CharField(max_length=50, null=True, blank=True)
    mpesa_checkout_request_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    metadata = models.JSONField(default=dict, blank=True)
    initiated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['action', 'status']),
            models.Index(fields=['payment_method', 'status']),
        ]

    def __str__(self):
        return f"{self.action} - {self.amount} ({self.status})"
    
    def mark_as_pending(self):
        """Mark transaction as pending."""
        self.status = 'pending'
        self.save()
    
    def mark_as_initiated(self):
        """Mark transaction as initiated (STK push sent)."""
        self.status = 'initiated'
        self.initiated_at = now()
        self.save()
    
    def mark_as_success(self):
        """Mark transaction as successful."""
        self.status = 'success'
        self.completed_at = now()
        self.save()
    
    def mark_as_failed(self):
        """Mark transaction as failed."""
        self.status = 'failed'
        self.completed_at = now()
        self.save()


class Conversation(TimeStampedModel):
    """
    Represents a conversation between a buyer and seller about a listing.
    Groups messages into organized threads.
    """
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='seller_conversations',
        db_index=True
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='buyer_conversations',
        db_index=True
    )
    listing = models.ForeignKey(
        'Listing',
        on_delete=models.CASCADE,
        related_name='conversations',
        db_index=True
    )
    subject = models.CharField(max_length=255, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False, db_index=True)
    
    class Meta:
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['seller', 'buyer']),
            models.Index(fields=['seller', 'is_archived']),
            models.Index(fields=['buyer', 'is_archived']),
        ]
        unique_together = [['seller', 'buyer', 'listing']]
    
    def __str__(self):
        return f"Conversation: {self.buyer.email} - {self.seller.email} about {self.listing.title}"


class Message(TimeStampedModel):
    """
    Stores messages for buyer-seller communication within a tenant's schema.
    Part of a Conversation between buyer and seller about a listing.
    """
    conversation = models.ForeignKey(
        'Conversation',
        on_delete=models.CASCADE,
        related_name='messages',
        db_index=True,
        null=True,
        blank=True
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        db_index=True
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
        db_index=True
    )
    listing = models.ForeignKey(
        'Listing',
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True,
        db_index=True
    )
    content = models.TextField(max_length=2000)
    is_read = models.BooleanField(default=False, db_index=True)
    is_typing = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='messages/', null=True, blank=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'is_read']),
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        return f"Message from {self.sender.email} to {self.receiver.email}"

    def mark_as_read(self):
        """Mark message as read."""
        if not self.is_read:
            self.is_read = True
            self.save()


class ShopAnalytics(TimeStampedModel):
    """
    Stores analytics data for shops, including sales, visits, and listings.
    """
    shop = models.OneToOneField(
        Shop,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    total_listings = models.PositiveIntegerField(default=0)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_visits = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Shop Analytics"
        verbose_name_plural = "Shop Analytics"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Analytics for {self.shop.name}"
    
    

class Payment(TimeStampedModel):
    """
    Legacy payment tracking model. Use Transaction for new payments.
    Kept for backward compatibility.
    """
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        db_index=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"{self.method} - {self.amount} ({self.status})"


class BlogCategory(models.Model):
    """
    Model for categorizing blog posts (e.g., 'Announcements', 'Student Life', 'Tips').
    This is separate from the product `Category` model.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name = "Blog Category"
        verbose_name_plural = "Blog Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    """
    Represents a single blog post in the marketing section of the site.
    """

    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True,
                            help_text="URL-friendly version of the title. Auto-generated if left blank.")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_posts')

    # For a classy design, a featured image is essential
    featured_image = models.ImageField(upload_to='blog/featured_images/', null=True, blank=True)

    # The main content. For rich text, consider a library like django-ckeditor.
    content = models.TextField()

    # A short summary shown on the blog list page.
    excerpt = models.CharField(max_length=250, blank=True)

    # Categorization
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')

    # Status for drafts vs. published posts
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.DRAFT)

    # Timestamps
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_on']  # Show the newest posts first

    def save(self, *args, **kwargs):
        # Auto-generate slug from title if it's not provided
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ListingTemplate(TimeStampedModel):
    """
    Seller template for quick listing creation.
    Allows sellers to save common listing attributes and reuse them.
    """
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='listing_templates',
        db_index=True
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='templates',
        db_index=True
    )
    name = models.CharField(max_length=255, help_text='Template name (e.g., "Electronics Bundle")')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='templates'
    )
    condition = models.CharField(
        max_length=20,
        choices=Listing.CONDITION_CHOICES,
        default='good'
    )
    description = models.TextField(
        blank=True,
        help_text='Template description (reusable text)'
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'shop', 'is_active']),
        ]
        unique_together = [['shop', 'name']]
    
    def __str__(self):
        return f"{self.name} ({self.shop.name})"
    
    def create_listing_from_template(self, title, price):
        """Create a new listing using this template."""
        return Listing.objects.create(
            title=title,
            seller=self.seller,
            shop=self.shop,
            category=self.category,
            condition=self.condition,
            description=self.description,
            price=price,
            status='draft'
        )


class ShippingCarrier(models.Model):
    """Shipping carrier options (Posta, Jiji, courier, etc)."""
    
    CARRIER_TYPES = [
        ('local_pickup', 'Local Pickup'),
        ('posta', 'Posta (National)'),
        ('jiji', 'Jiji Courier'),
        ('ups', 'UPS'),
        ('fedex', 'FedEx'),
        ('dhl', 'DHL'),
        ('custom', 'Custom Courier'),
    ]
    
    name = models.CharField(max_length=100, choices=CARRIER_TYPES, unique=True)
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, db_index=True)
    estimated_days_min = models.IntegerField(default=1, help_text='Min delivery days')
    estimated_days_max = models.IntegerField(default=5, help_text='Max delivery days')
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class ShippingRate(models.Model):
    """Shipping rate by weight range and carrier."""
    
    carrier = models.ForeignKey(
        ShippingCarrier,
        on_delete=models.CASCADE,
        related_name='rates'
    )
    weight_min_kg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    weight_max_kg = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    price_kes = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['weight_min_kg']
        unique_together = [['carrier', 'weight_min_kg', 'weight_max_kg']]
    
    def __str__(self):
        return f'{self.carrier.display_name} {self.weight_min_kg}-{self.weight_max_kg}kg: {self.price_kes} KES'


class ShippingOption(TimeStampedModel):
    """Shipping options selected for a listing."""
    
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='shipping_options'
    )
    carrier = models.ForeignKey(ShippingCarrier, on_delete=models.PROTECT)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = [['listing', 'carrier']]
    
    def __str__(self):
        return f'{self.listing.title} - {self.carrier.display_name}'


class Shipment(TimeStampedModel):
    """Track shipments for orders."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Pickup'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Delivery Failed'),
        ('returned', 'Returned'),
    ]
    
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='shipment'
    )
    carrier = models.ForeignKey(ShippingCarrier, on_delete=models.PROTECT)
    tracking_number = models.CharField(max_length=100, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    actual_delivery = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_number', 'status']),
        ]
    
    def __str__(self):
        return f'#{self.tracking_number} - {self.get_status_display()}'


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
    
    is_active = models.BooleanField(default=True, db_index=True)
    condition_min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    condition_max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    condition_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    action_param_1 = models.CharField(max_length=255, blank=True)
    action_param_2 = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'shop', 'is_active']),
            models.Index(fields=['rule_type']),
        ]
    
    def __str__(self):
        return f'{self.name} ({self.get_rule_type_display()})'


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
    
    min_acceptable_price_percent = models.IntegerField(default=80)
    auto_decline_below_percent = models.BooleanField(default=False)
    auto_counter_offer = models.BooleanField(default=False)
    counter_offer_percent = models.IntegerField(default=10)
    
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        unique_together = [['shop', 'seller']]
    
    def __str__(self):
        return f'Offer Rules - {self.shop.name}'
    
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
