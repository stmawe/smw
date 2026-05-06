from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.auth.models import AbstractUser


class Client(TenantMixin):
    """
    Represents a tenant (University, Area, or Shop).
    """
    name = models.CharField(max_length=255, unique=True, db_index=True)
    tenant_type = models.CharField(
        max_length=20,
        choices=[
            ('university', 'University'),
            ('location', 'Location/Area'),
            ('shop', 'Shop')
        ],
        db_index=True
    )
    parent_tenant = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='child_tenants',
        help_text='Parent tenant for shops (linked to University or Location)'
    )
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    auto_create_schema = True

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant_type', 'on_trial']),
            models.Index(fields=['parent_tenant', 'tenant_type']),
        ]

    def __str__(self):
        return self.name
    
    def get_users(self):
        """Get all users in this tenant."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # For now, return users with matching role
        if self.tenant_type == 'university':
            return User.objects.filter(role='university_admin')
        elif self.tenant_type == 'location':
            return User.objects.filter(role='area_admin')
        return User.objects.none()


class ClientDomain(DomainMixin):
    """
    Represents a domain associated with a tenant.
    """
    class Meta:
        ordering = ['domain']

    def __str__(self):
        return self.domain


class User(AbstractUser):
    """
    Custom User Model.
    """
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('superadmin', 'SuperAdmin'),
        ('university_admin', 'University Admin'),
        ('area_admin', 'Area Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='buyer')

    # Resolve reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )


class Entity(models.Model):
    """
    Represents an institution (university, location, NGO, etc.) that can host
    shops on the platform.

    Two creation paths:
    - Admin-created: status=active immediately, Cloudflare DNS created on save.
    - Self-registered: status=pending until main admin approves.

    is_active is derived from status in save() — never set directly.
    """

    STATUS_PENDING   = 'pending'
    STATUS_ACTIVE    = 'active'
    STATUS_SUSPENDED = 'suspended'
    STATUS_CHOICES = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_ACTIVE,    'Active'),
        (STATUS_SUSPENDED, 'Suspended'),
    ]

    name        = models.CharField(max_length=255)
    entity_type = models.CharField(
        max_length=100,
        help_text='Free-form type label, e.g. "University", "Location", "NGO"'
    )
    subdomain   = models.SlugField(
        max_length=63,
        unique=True,
        help_text='Subdomain slug — becomes {subdomain}.smw.pgwiz.cloud'
    )
    admin_user  = models.ForeignKey(
        'app.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='administered_entities',
        help_text='Designated admin for this entity'
    )
    status      = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    is_active   = models.BooleanField(
        default=False,
        help_text='Derived from status in save() — do not set directly'
    )
    created_by  = models.ForeignKey(
        'app.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_entities',
        help_text='NULL for self-registrations; set to admin user for admin-created entities'
    )
    city        = models.CharField(max_length=100, blank=True)
    country     = models.CharField(max_length=100, blank=True)
    website     = models.URLField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'entities'
        ordering = ['name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['is_active', 'name']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Keep is_active in sync with status — never set is_active directly
        self.is_active = (self.status == self.STATUS_ACTIVE)
        super().save(*args, **kwargs)


class Category(models.Model):
    """
    Shared category model for organizing listings.
    """
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


# ============================================================
# THEME SYSTEM MODELS - Dynamic Design Customization
# ============================================================
# Allows admins to create themes, mock designs, and control
# design tokens via database instead of hardcoded CSS.
# ============================================================

class ThemeToken(models.Model):
    """
    Individual design token (color, spacing, font, effect, etc.)
    Can be organized into themes for different pages/contexts
    """
    
    TOKEN_CATEGORIES = [
        ('color', 'Color'),
        ('spacing', 'Spacing'),
        ('typography', 'Typography'),
        ('radius', 'Border Radius'),
        ('shadow', 'Shadow'),
        ('effect', 'Effect/Filter'),
        ('layout', 'Layout'),
    ]
    
    # Token identity
    name = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="e.g., 'primary-blue', 'space-4', 'font-body'"
    )
    category = models.CharField(max_length=20, choices=TOKEN_CATEGORIES)
    description = models.TextField(blank=True, help_text="What this token is used for")
    
    # Default value
    default_value = models.CharField(
        max_length=500,
        help_text="CSS value: hex color, px value, font stack, etc."
    )
    
    # Metadata
    is_global = models.BooleanField(
        default=True,
        help_text="If True, affects all pages; if False, can be overridden per-theme"
    )
    css_custom_property = models.CharField(
        max_length=100,
        unique=True,
        help_text="CSS custom property name: --primary-blue"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class Theme(models.Model):
    """
    A collection of design token values that can be applied to pages.
    Admin can create multiple themes and switch between them.
    """
    
    THEME_TYPES = [
        ('global', 'Global Site Theme'),
        ('page-specific', 'Page-Specific Override'),
        ('variant', 'Design Variant'),
        ('accessibility', 'Accessibility Mode'),
    ]
    
    # Theme identity
    name = models.CharField(max_length=200, help_text="e.g., 'Dark Luxury', 'Light Enterprise'")
    slug = models.SlugField(unique=True, help_text="URL-safe identifier")
    description = models.TextField(blank=True)
    theme_type = models.CharField(max_length=20, choices=THEME_TYPES, default='global')
    
    # Token overrides - store as JSON
    token_overrides = models.JSONField(
        default=dict,
        blank=True,
        help_text="Map of token_name -> value overrides"
    )
    
    # Template overrides - custom CSS for this theme
    custom_css = models.TextField(
        blank=True,
        help_text="Additional CSS rules specific to this theme"
    )
    
    # Metadata
    is_active = models.BooleanField(default=False, help_text="Is this the current active theme?")
    is_public = models.BooleanField(default=False, help_text="Should this be visible to users?")
    created_by = models.ForeignKey('app.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_active', '-created_at']
    
    def __str__(self):
        return f"{self.name} {'(Active)' if self.is_active else ''}"
    
    def save(self, *args, **kwargs):
        # Only one theme can be active at a time
        if self.is_active:
            Theme.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
        # Invalidate cache when theme changes
        from django.core.cache import cache
        cache.delete('active_theme_css')
    
    def get_merged_tokens(self):
        """
        Merge default tokens with this theme's overrides.
        Returns dict of {css_custom_property: value}
        """
        tokens = {}
        for token in ThemeToken.objects.all():
            # Start with default
            value = token.default_value
            # Override if exists in this theme
            if token.name in self.token_overrides:
                value = self.token_overrides[token.name]
            tokens[token.css_custom_property] = value
        return tokens
    
    def generate_css(self):
        """
        Generate complete CSS for this theme.
        Used in templates to inject theme via <style> tag.
        """
        tokens = self.get_merged_tokens()
        css_vars = "\n  ".join([f"{prop}: {value};" for prop, value in tokens.items()])
        
        css = f"""
:root {{
  {css_vars}
}}

{self.custom_css}
"""
        return css


class PageThemeAssignment(models.Model):
    """
    Maps a page/route to a specific theme override.
    Allows different pages to have different themes.
    """
    
    PAGE_TYPES = [
        ('homepage', 'Homepage'),
        ('explore', 'Explore/Directory'),
        ('listings', 'Listings'),
        ('shop-detail', 'Shop Detail'),
        ('listing-detail', 'Listing Detail'),
        ('about', 'About'),
        ('contact', 'Contact'),
        ('admin', 'Admin Dashboard'),
        ('custom', 'Custom Page'),
    ]
    
    page_type = models.CharField(
        max_length=50,
        choices=PAGE_TYPES,
        unique=True
    )
    page_route = models.CharField(
        max_length=255,
        blank=True,
        help_text="Django URL name or pattern. Leave blank for page_type auto-detection"
    )
    
    # Theme assignment
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True)
    override_enabled = models.BooleanField(
        default=True,
        help_text="If False, uses global active theme"
    )
    
    # Admin notes
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['page_type']
        verbose_name = 'Page Theme Assignment'
        verbose_name_plural = 'Page Theme Assignments'
    
    def __str__(self):
        return f"{self.page_type} → {self.theme.name if self.theme else 'Global'}"


class ThemeComponentLibrary(models.Model):
    """
    Reusable component templates with theme-aware CSS.
    Stores mock/draft versions of components before deployment.
    """
    
    # Component identity
    name = models.CharField(max_length=200, help_text="e.g., 'NavBar', 'ProductCard'")
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    # Component code
    html_template = models.TextField(help_text="Template HTML (can use Django template syntax)")
    inline_css = models.TextField(blank=True, help_text="CSS specific to this component")
    inline_js = models.TextField(blank=True, help_text="JavaScript for interactivity")
    
    # Version control for mocking
    version = models.IntegerField(default=1, help_text="Version number for iterations")
    is_published = models.BooleanField(default=False, help_text="Is this version live?")
    is_draft = models.BooleanField(default=True, help_text="Is this a draft/mock?")
    
    # Metadata
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey('app.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_published', 'name', '-version']
        unique_together = [('slug', 'version')]
    
    def __str__(self):
        status = "Draft" if self.is_draft else "Published"
        return f"{self.name} v{self.version} ({status})"
    
    def publish(self):
        """Publish this component version (mark old versions as not published)"""
        ThemeComponentLibrary.objects.filter(slug=self.slug).update(is_published=False)
        self.is_published = True
        self.is_draft = False
        self.save()


class ThemeChangeLog(models.Model):
    """
    Audit trail of theme modifications for design review.
    """
    
    CHANGE_TYPES = [
        ('token-update', 'Token Value Changed'),
        ('css-update', 'Custom CSS Updated'),
        ('theme-created', 'Theme Created'),
        ('theme-activated', 'Theme Activated'),
        ('theme-updated', 'Theme Updated'),
        ('theme-published', 'Theme Published'),
        ('theme-unpublished', 'Theme Unpublished'),
        ('theme-deleted', 'Theme Deleted'),
        ('component-mock', 'Component Mocked'),
        ('component-published', 'Component Published'),
    ]
    
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE)
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    
    # What changed
    changed_field = models.CharField(max_length=100, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    # Who and when
    changed_by = models.ForeignKey('app.User', on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True, help_text="Why this change was made")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.theme.name}: {self.change_type} @ {self.created_at}"


# ============================================================
# ADMIN AUDIT & ACTIVITY LOGGING MODELS
# ============================================================
# Comprehensive tracking of all admin actions for security,
# compliance, and activity monitoring.
# ============================================================

class AdminAuditLog(models.Model):
    """
    Detailed audit trail of all admin actions.
    Tracks WHO did WHAT to WHICH object and WHEN with before/after values.
    """
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('restore', 'Restore'),
        ('export', 'Export'),
        ('bulk_action', 'Bulk Action'),
        ('permission_grant', 'Permission Granted'),
        ('permission_revoke', 'Permission Revoked'),
        ('login', 'Admin Login'),
        ('logout', 'Admin Logout'),
        ('failed_auth', 'Failed Auth Attempt'),
        ('setting_change', 'Settings Changed'),
        ('ban_user', 'User Banned'),
        ('unban_user', 'User Unbanned'),
        ('approve_listing', 'Listing Approved'),
        ('reject_listing', 'Listing Rejected'),
        ('feature_listing', 'Listing Featured'),
        ('unfeature_listing', 'Listing Unfeatured'),
        ('process_refund', 'Refund Processed'),
        ('other', 'Other'),
    ]
    
    # Who performed the action
    admin_user = models.ForeignKey(
        'app.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_audit_logs'
    )
    admin_username = models.CharField(max_length=150, help_text="Snapshot of username at time of action")
    
    # What action
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    action_label = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable action description (e.g., 'Approved listing #123')"
    )
    
    # What object was affected
    content_type = models.CharField(
        max_length=100,
        help_text="Model name (e.g., 'User', 'Shop', 'Listing')"
    )
    object_id = models.CharField(max_length=255, help_text="ID of affected object")
    object_str = models.CharField(
        max_length=500,
        blank=True,
        help_text="String representation of object at time of action"
    )
    
    # Changes made
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dict of {field: {old: value, new: value}}"
    )
    old_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="Complete snapshot of object before change"
    )
    new_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="Complete snapshot of object after change"
    )
    
    # Context
    reason = models.TextField(blank=True, help_text="Why the action was taken (from form or comment)")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, help_text="Browser/client info")
    
    # Relationships (for bulk actions)
    related_objects = models.JSONField(
        default=list,
        blank=True,
        help_text="List of related object IDs affected (for bulk ops)"
    )
    
    # Metadata
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('partial_success', 'Partial Success'),
            ('error', 'Error'),
            ('pending', 'Pending'),
        ],
        default='success'
    )
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.admin_username} {self.action} {self.content_type}#{self.object_id}"
    
    def get_change_summary(self):
        """Returns human-readable summary of what changed"""
        if not self.changes:
            return f"{self.get_action_display()} {self.object_str}"
        
        changed_fields = list(self.changes.keys())
        if len(changed_fields) == 1:
            field = changed_fields[0]
            change = self.changes[field]
            return f"Changed {field} from '{change.get('old')}' to '{change.get('new')}'"
        else:
            return f"Modified {len(changed_fields)} fields"


class AdminActivityFeed(models.Model):
    """
    High-level activity feed for admin dashboard.
    Simpler than AdminAuditLog - for displaying activity timeline.
    """
    
    ACTIVITY_TYPES = [
        ('login', 'Admin Logged In'),
        ('logout', 'Admin Logged Out'),
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('banned', 'User Banned'),
        ('feature', 'Featured'),
        ('unfeature', 'Unfeatured'),
        ('refund', 'Refund Processed'),
        ('system', 'System Event'),
    ]
    
    # Who and what
    admin_user = models.ForeignKey(
        'app.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_feed'
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    
    # What was affected
    content_type = models.CharField(max_length=100, help_text="e.g., User, Shop, Listing")
    object_id = models.CharField(max_length=255)
    object_title = models.CharField(max_length=500, blank=True, help_text="e.g., user email, shop name, listing title")
    
    # Display
    description = models.CharField(
        max_length=500,
        help_text="Short summary for dashboard (e.g., 'Admin approved listing #123')"
    )
    
    # Icon & color for UI
    icon = models.CharField(
        max_length=50,
        blank=True,
        default='activity',
        help_text="Bootstrap icon name (bi-*)"
    )
    severity = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Info'),
            ('success', 'Success'),
            ('warning', 'Warning'),
            ('danger', 'Danger'),
        ],
        default='info'
    )
    
    # Link back to related object
    link_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Admin URL to the affected object"
    )
    
    # For grouping related activities
    batch_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="ID for grouping related bulk actions"
    )
    
    # Metadata
    is_visible = models.BooleanField(default=True, help_text="Show in activity feed?")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.admin_user.username if self.admin_user else 'System'} - {self.description}"


# ============================================================
# M-PESA PAYMENT TRANSACTION TRACKING
# ============================================================
# Comprehensive tracking of all M-PESA Daraja Gateway
# transactions: STK Push, B2C, Reversals, etc.
# ============================================================

class MpesaTransaction(models.Model):
    """
    Tracks all M-PESA payment transactions.
    
    Supports:
    - STK Push (Lipa Na M-PESA Online) for customer payments
    - STK Status polling for payment status updates
    - Reversals for undoing payments
    - Dynamic QR Code transactions
    - Account Balance inquiries
    - Transaction Status lookups
    """
    
    TYPE_CHOICES = [
        ('stk_push', 'STK Push - Customer Payment Prompt'),
        ('stk_status', 'STK Status - Payment Status Poll'),
        ('reversal', 'Reversal - Undo Transaction'),
        ('qr_code', 'QR Code - Dynamic QR Generation'),
        ('balance', 'Account Balance - Balance Inquiry'),
        ('transaction_status', 'Transaction Status - Lookup'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending - Awaiting response'),
        ('success', 'Success - Payment completed'),
        ('failed', 'Failed - Payment rejected or cancelled'),
    ]
    
    # ===== Transaction Identifiers =====
    user = models.ForeignKey(
        'app.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mpesa_transactions',
        help_text='User initiating the transaction'
    )
    shop = models.ForeignKey(
        'app.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mpesa_transactions',
        help_text='Shop associated with transaction (if any)'
    )
    
    # ===== Transaction Type & Status =====
    transaction_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        db_index=True,
        help_text='Type of M-PESA transaction'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text='Current transaction status'
    )
    
    # ===== Payment Details =====
    phone = models.CharField(
        max_length=15,
        db_index=True,
        help_text='Customer/recipient phone in format 254XXXXXXXXX'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount in KES'
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text='Transaction reference / order ID'
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text='Human-readable description of transaction'
    )
    
    # ===== M-PESA API Responses =====
    merchant_request_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text='MerchantRequestID from M-PESA API'
    )
    checkout_request_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        unique=True,
        help_text='CheckoutRequestID from STK Push (for polling status)'
    )
    conversation_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text='ConversationID from M-PESA API response'
    )
    originator_conversation_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='OriginatorConversationID from M-PESA API'
    )
    
    # ===== Payment Result =====
    receipt = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        help_text='M-PESA receipt number (on success)'
    )
    result_code = models.CharField(
        max_length=10,
        blank=True,
        help_text='Result code from M-PESA API'
    )
    result_description = models.TextField(
        blank=True,
        help_text='Result description from M-PESA (success/failure reason)'
    )
    
    # ===== API Request/Response Logging =====
    request_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text='Complete request sent to M-PESA API'
    )
    response_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text='Complete response from M-PESA API'
    )
    
    # ===== Rate Limit Information =====
    rate_limit_remaining = models.IntegerField(
        null=True,
        blank=True,
        help_text='Remaining API quota after this request'
    )
    rate_limit_total = models.IntegerField(
        null=True,
        blank=True,
        help_text='Total daily API quota'
    )
    rate_limit_reset = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the rate limit counter resets'
    )
    
    # ===== Timestamps =====
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When payment was completed (success or failed)'
    )
    
    # ===== Context & Audit =====
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address when transaction was initiated'
    )
    user_agent = models.TextField(
        blank=True,
        help_text='Browser/client info'
    )
    notes = models.TextField(
        blank=True,
        help_text='Admin notes or transaction details'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'M-PESA Transaction'
        verbose_name_plural = 'M-PESA Transactions'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['phone', '-created_at']),
            models.Index(fields=['receipt']),
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['transaction_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.phone} KES {self.amount} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Set completed_at when status changes to success/failed
        if self.status in ['success', 'failed'] and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)
    
    @classmethod
    def create_from_stk_push(cls, user, phone, amount, reference, response, ip_address='', user_agent=''):
        """
        Create a transaction record from STK Push API response.
        
        Args:
            user: User initiating the payment
            phone: Customer phone number
            amount: Amount in KES
            reference: Transaction reference
            response: Response dict from MpesaClient.stk_push()
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            MpesaTransaction instance (saved to database)
        """
        transaction = cls(
            user=user,
            phone=phone,
            amount=amount,
            reference=reference,
            transaction_type='stk_push',
            status='pending',
            merchant_request_id=response.get('MerchantRequestID'),
            checkout_request_id=response.get('CheckoutRequestID'),
            response_payload=response,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        transaction.save()
        return transaction
    
    def update_from_status(self, status_response):
        """
        Update transaction with STK Status poll response.
        
        Args:
            status_response: Response dict from MpesaClient.stk_status()
        """
        self.status = status_response.get('status', 'pending')
        self.receipt = status_response.get('receipt') or self.receipt
        self.result_code = status_response.get('resultCode') or self.result_code
        self.result_description = status_response.get('resultDesc') or self.result_description
        self.response_payload = status_response
        self.save()
    
    def get_status_label(self):
        """Return Bootstrap badge class for status"""
        status_map = {
            'pending': 'warning',
            'success': 'success',
            'failed': 'danger',
        }
        return status_map.get(self.status, 'secondary')
