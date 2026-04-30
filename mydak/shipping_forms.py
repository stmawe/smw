"""Shipping selection forms."""

from django import forms
from mydak.models import ShippingCarrier, ShippingOption


class ShippingSelectionForm(forms.Form):
    """Form for selecting shipping options for a listing."""
    
    weight_kg = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Item weight (optional, default 0.5kg)',
            'class': 'form-control',
            'min': '0',
            'step': '0.1',
        })
    )
    
    carriers = forms.ModelMultipleChoiceField(
        queryset=ShippingCarrier.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        help_text='Select at least one shipping carrier'
    )
    
    def clean_weight_kg(self):
        weight = self.cleaned_data.get('weight_kg')
        if weight is not None and weight < 0:
            raise forms.ValidationError('Weight cannot be negative')
        return weight


class ShippingOptionForm(forms.ModelForm):
    """Form for managing shipping options."""
    
    class Meta:
        model = ShippingOption
        fields = ['carrier', 'weight_kg', 'is_available']
        widgets = {
            'carrier': forms.Select(attrs={'class': 'form-control'}),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.1',
            }),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
