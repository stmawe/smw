"""Shop creation models and forms."""

from django import forms
from mydak.models import Shop
from django.core.exceptions import ValidationError


class ShopCreationForm(forms.ModelForm):
    """
    Form for creating a new shop during onboarding.
    """
    
    class Meta:
        model = Shop
        fields = ['name', 'domain', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Shop Name',
                'class': 'form-control',
                'required': True,
            }),
            'domain': forms.TextInput(attrs={
                'placeholder': 'shop-name (lowercase, no spaces)',
                'class': 'form-control',
                'required': True,
                'pattern': '^[a-z0-9-]+$',
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Tell customers about your shop',
                'class': 'form-control',
                'rows': 4,
            }),
        }
    
    def clean_domain(self):
        domain = self.cleaned_data.get('domain', '').lower().strip()
        
        # Validate domain format
        if not domain or len(domain) < 3:
            raise ValidationError('Domain must be at least 3 characters')
        
        if not all(c.isalnum() or c == '-' for c in domain):
            raise ValidationError('Domain can only contain letters, numbers, and hyphens')
        
        if domain.startswith('-') or domain.endswith('-'):
            raise ValidationError('Domain cannot start or end with hyphen')
        
        # Check if domain already exists
        if Shop.objects.filter(domain=domain).exists():
            raise ValidationError('This domain is already taken')
        
        return domain
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        
        if not name or len(name) < 2:
            raise ValidationError('Shop name must be at least 2 characters')
        
        if len(name) > 100:
            raise ValidationError('Shop name must be 100 characters or less')
        
        return name


class ShopEditForm(forms.ModelForm):
    """Form for editing shop details."""
    
    class Meta:
        model = Shop
        fields = ['name', 'description', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }
