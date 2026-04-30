"""Bulk listing upload forms."""

import csv
import io
from django import forms
from django.core.exceptions import ValidationError
from mydak.models import Listing, Category


class BulkListingUploadForm(forms.Form):
    """Form for bulk listing CSV upload."""
    
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload CSV with columns: title, price, category, condition, description, image_url (optional)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv',
            'required': True,
        })
    )
    
    action = forms.ChoiceField(
        choices=[
            ('preview', 'Preview Only'),
            ('import', 'Import All'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    def clean_csv_file(self):
        """Validate CSV file format."""
        file = self.cleaned_data.get('csv_file')
        
        if not file:
            raise ValidationError('No file selected')
        
        if not file.name.endswith('.csv'):
            raise ValidationError('File must be CSV format')
        
        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError('File size must be less than 5MB')
        
        return file
    
    def parse_csv(self):
        """Parse and validate CSV data."""
        file = self.cleaned_data.get('csv_file')
        if not file:
            return []
        
        try:
            decoded = file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            rows = list(reader)
        except (UnicodeDecodeError, csv.Error) as e:
            raise ValidationError(f'Invalid CSV format: {str(e)}')
        
        if not rows:
            raise ValidationError('CSV is empty')
        
        # Validate required columns
        required_cols = {'title', 'price', 'category', 'condition'}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            raise ValidationError(
                f'CSV must contain columns: {", ".join(required_cols)}'
            )
        
        return rows


class BulkListingValidator:
    """Validate and prepare bulk listing data."""
    
    CONDITION_CHOICES = dict(Listing.CONDITION_CHOICES)
    
    @staticmethod
    def validate_row(row, row_num):
        """Validate a single CSV row."""
        errors = []
        
        # Title validation
        title = row.get('title', '').strip()
        if not title:
            errors.append(f'Row {row_num}: Title is required')
        elif len(title) < 5:
            errors.append(f'Row {row_num}: Title must be at least 5 characters')
        elif len(title) > 200:
            errors.append(f'Row {row_num}: Title must be 200 characters or less')
        
        # Price validation
        try:
            price = float(row.get('price', 0))
            if price < 0:
                errors.append(f'Row {row_num}: Price must be positive')
        except (ValueError, TypeError):
            errors.append(f'Row {row_num}: Price must be a valid number')
        
        # Category validation
        category_name = row.get('category', '').strip()
        if not category_name:
            errors.append(f'Row {row_num}: Category is required')
        else:
            try:
                Category.objects.get(name__iexact=category_name)
            except Category.DoesNotExist:
                errors.append(
                    f'Row {row_num}: Category "{category_name}" not found. '
                    f'Valid categories: {", ".join(Category.objects.values_list("name", flat=True))}'
                )
        
        # Condition validation
        condition = row.get('condition', '').strip()
        if not condition:
            errors.append(f'Row {row_num}: Condition is required')
        elif condition not in BulkListingValidator.CONDITION_CHOICES:
            valid = ', '.join(BulkListingValidator.CONDITION_CHOICES.keys())
            errors.append(f'Row {row_num}: Invalid condition. Valid values: {valid}')
        
        # Description validation (optional but recommended)
        description = row.get('description', '').strip()
        if description and len(description) > 5000:
            errors.append(f'Row {row_num}: Description must be 5000 characters or less')
        
        return errors
    
    @staticmethod
    def prepare_listing_data(row):
        """Convert CSV row to listing data dict."""
        category = Category.objects.get(name__iexact=row.get('category', '').strip())
        
        return {
            'title': row.get('title', '').strip(),
            'price': float(row.get('price', 0)),
            'category': category,
            'condition': row.get('condition', '').strip(),
            'description': row.get('description', '').strip(),
            'image_url': row.get('image_url', '').strip(),
        }


class BulkListingPreviewForm(forms.Form):
    """Form to confirm bulk import after preview."""
    
    confirm = forms.BooleanField(
        label='I confirm these listings are correct and ready to import',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    listing_count = forms.IntegerField(widget=forms.HiddenInput())
