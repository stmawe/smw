from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.auth.models import AbstractUser


class Client(TenantMixin):
    """
    Represents a tenant (University or Area).
    """
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=20, choices=[('university', 'University'), ('area', 'Area')])
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)

    auto_create_schema = True

    def __str__(self):
        return self.name


class ClientDomain(DomainMixin):
    """
    Represents a domain associated with a tenant.
    """
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