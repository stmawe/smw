"""Payment forms for M-Pesa bootstrap implementation."""

from django import forms
from mydak.models import Transaction


class PaymentInitiateForm(forms.Form):
    """Form to initiate M-Pesa payment."""
    
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '254712345678',
            'class': 'form-control',
            'pattern': '[0-9]{12}',
            'title': 'Phone must be in format 254XXXXXXXXX'
        }),
        help_text='Phone number in format 254XXXXXXXXX (12 digits)'
    )
    
    payment_method = forms.ChoiceField(
        choices=[('mpesa', 'M-Pesa')],
        widget=forms.RadioSelect(),
        help_text='Currently only M-Pesa is supported'
    )
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        
        if not phone.startswith('254'):
            raise forms.ValidationError('Phone must start with 254 (Kenya country code)')
        
        if len(phone) != 12:
            raise forms.ValidationError('Phone must be exactly 12 digits')
        
        if not phone.isdigit():
            raise forms.ValidationError('Phone must contain only digits')
        
        return phone


class PaymentStatusForm(forms.Form):
    """Form to check payment status (for manual polling)."""
    
    checkout_request_id = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'readonly': True,
            'class': 'form-control'
        })
    )
