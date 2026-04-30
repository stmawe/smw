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