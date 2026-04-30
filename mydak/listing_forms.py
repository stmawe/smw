"""Listing forms for marketplace."""

from django import forms
from mydak.models import Listing, Category


class ListingCreationForm(forms.ModelForm):
    """Form for creating new listings."""
    
    class Meta:
        model = Listing
        fields = ['title', 'category', 'description', 'price', 'condition', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'What are you selling?',
                'class': 'form-control',
                'required': True,
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe your item in detail',
                'class': 'form-control',
                'rows': 5,
            }),
            'price': forms.NumberInput(attrs={
                'placeholder': '0.00',
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'required': True,
            }),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('Price must be positive')
        return price
    
    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise forms.ValidationError('Title must be at least 5 characters')
        if len(title) > 200:
            raise forms.ValidationError('Title must be 200 characters or less')
        return title


class ListingEditForm(forms.ModelForm):
    """Form for editing listings."""
    
    class Meta:
        model = Listing
        fields = ['title', 'category', 'description', 'price', 'condition', 'image', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class ListingSearchForm(forms.Form):
    """Form for searching and filtering listings."""
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search listings...',
            'class': 'form-control',
        })
    )
    
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    condition = forms.ChoiceField(
        required=False,
        choices=[('', 'All Conditions')] + Listing.CONDITION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    price_min = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min price',
            'class': 'form-control',
            'step': '0.01',
        })
    )
    
    price_max = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max price',
            'class': 'form-control',
            'step': '0.01',
        })
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('recent', 'Most Recent'),
            ('price_low', 'Price: Low to High'),
            ('price_high', 'Price: High to Low'),
            ('popular', 'Most Popular'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
