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