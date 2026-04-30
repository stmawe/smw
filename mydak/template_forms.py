"""Listing template forms."""

from django import forms
from mydak.models import ListingTemplate, Category


class ListingTemplateForm(forms.ModelForm):
    """Form for creating/editing listing templates."""
    
    class Meta:
        model = ListingTemplate
        fields = ['name', 'category', 'condition', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Template name (e.g., "Used Electronics")',
                'class': 'form-control',
                'required': True,
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'placeholder': 'Template description (will be used for all listings created from this template)',
                'class': 'form-control',
                'rows': 5,
            }),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 3:
            raise forms.ValidationError('Template name must be at least 3 characters')
        if len(name) > 255:
            raise forms.ValidationError('Template name must be 255 characters or less')
        return name


class CreateListingFromTemplateForm(forms.Form):
    """Form for creating a listing from a template."""
    
    template_id = forms.IntegerField(widget=forms.HiddenInput())
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Listing title',
            'class': 'form-control',
            'required': True,
        })
    )
    
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'placeholder': '0.00',
            'class': 'form-control',
            'min': '0',
            'step': '0.01',
            'required': True,
        })
    )
    
    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise forms.ValidationError('Title must be at least 5 characters')
        if len(title) > 200:
            raise forms.ValidationError('Title must be 200 characters or less')
        return title
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('Price must be positive')
        return price
