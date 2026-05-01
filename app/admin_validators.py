"""
Admin form validators for comprehensive validation.
Includes both client-side (JavaScript) validation and server-side validators.
"""

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import re


class AdminFormValidators:
    """Validators for admin forms."""
    
    @staticmethod
    def validate_email_unique(email, exclude_id=None):
        """Check if email is unique (or belongs to the same user)."""
        query = User.objects.filter(email=email)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        if query.exists():
            raise ValidationError(_('Email already in use.'))
    
    @staticmethod
    def validate_username_unique(username, exclude_id=None):
        """Check if username is unique."""
        query = User.objects.filter(username=username)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        if query.exists():
            raise ValidationError(_('Username already in use.'))
    
    @staticmethod
    def validate_strong_password(password):
        """
        Enforce strong password requirements:
        - Minimum 12 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(password) < 12:
            raise ValidationError(_('Password must be at least 12 characters long.'))
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_('Password must contain at least one uppercase letter.'))
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(_('Password must contain at least one lowercase letter.'))
        
        if not re.search(r'\d', password):
            raise ValidationError(_('Password must contain at least one digit.'))
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/`~]', password):
            raise ValidationError(_('Password must contain at least one special character.'))
    
    @staticmethod
    def validate_domain_format(domain):
        """Validate domain name format."""
        domain_pattern = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
        if not re.match(domain_pattern, domain.lower()):
            raise ValidationError(_('Invalid domain format.'))
    
    @staticmethod
    def validate_url_format(url):
        """Validate URL format."""
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url.lower()):
            raise ValidationError(_('Invalid URL format.'))
    
    @staticmethod
    def validate_price_format(price):
        """Validate price is a positive number with up to 2 decimal places."""
        try:
            price_float = float(price)
            if price_float < 0:
                raise ValidationError(_('Price cannot be negative.'))
            # Check decimal places
            if len(str(price).split('.')[-1]) > 2:
                raise ValidationError(_('Price can have at most 2 decimal places.'))
        except (ValueError, TypeError):
            raise ValidationError(_('Invalid price format.'))
    
    @staticmethod
    def validate_slug_format(slug):
        """Validate slug contains only lowercase letters, numbers, and hyphens."""
        slug_pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
        if not re.match(slug_pattern, slug):
            raise ValidationError(_('Slug can only contain lowercase letters, numbers, and hyphens.'))
    
    @staticmethod
    def validate_phone_format(phone):
        """Validate phone number format."""
        phone_pattern = r'^\+?1?\d{9,15}$'
        if not re.match(phone_pattern, phone.replace(' ', '').replace('-', '')):
            raise ValidationError(_('Invalid phone number format.'))


class AdminFormValidationRules:
    """Client-side validation rules (JSON format for JavaScript)."""
    
    @staticmethod
    def get_validation_rules():
        """Return validation rules for form fields."""
        return {
            'email': {
                'required': True,
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'message': 'Please enter a valid email address.',
            },
            'username': {
                'required': True,
                'min_length': 3,
                'max_length': 30,
                'pattern': r'^[a-zA-Z0-9_-]+$',
                'message': 'Username can only contain letters, numbers, underscores, and hyphens.',
            },
            'password': {
                'required': True,
                'min_length': 12,
                'pattern': r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/`~])',
                'message': 'Password must contain uppercase, lowercase, digit, and special character.',
            },
            'domain': {
                'required': True,
                'pattern': r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$',
                'message': 'Please enter a valid domain name.',
            },
            'url': {
                'required': True,
                'pattern': r'^https?://[^\s/$.?#].[^\s]*$',
                'message': 'Please enter a valid URL.',
            },
            'price': {
                'required': True,
                'min': 0,
                'pattern': r'^\d+(\.\d{1,2})?$',
                'message': 'Please enter a valid price.',
            },
            'phone': {
                'required': False,
                'pattern': r'^\+?1?\d{9,15}$',
                'message': 'Please enter a valid phone number.',
            },
        }


def get_form_validation_js():
    """
    Generate JavaScript for client-side form validation.
    Include this in your template with {% include 'admin/components/form_validation.js' %}
    """
    return """
<script>
// Client-side form validation for admin forms
(function() {
    const validationRules = {
        email: {
            required: true,
            pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$/,
            message: 'Please enter a valid email address.'
        },
        username: {
            required: true,
            minLength: 3,
            maxLength: 30,
            pattern: /^[a-zA-Z0-9_-]+$/,
            message: 'Username can only contain letters, numbers, underscores, and hyphens.'
        },
        password: {
            required: true,
            minLength: 12,
            pattern: /^(?=.*[A-Z])(?=.*[a-z])(?=.*\\d)(?=.*[!@#$%^&*()_+\\-=\\[\\]{};:'",.<>?\/`~])/,
            message: 'Password must contain uppercase, lowercase, digit, and special character.'
        },
        domain: {
            required: true,
            pattern: /^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\\.)+[a-z]{2,}$/i,
            message: 'Please enter a valid domain name.'
        },
        price: {
            required: true,
            min: 0,
            pattern: /^\\d+(\\.\\d{1,2})?$/,
            message: 'Please enter a valid price.'
        }
    };
    
    function validateField(field) {
        const fieldName = field.name || field.id;
        const rules = validationRules[fieldName];
        const value = field.value.trim();
        
        if (!rules) return true;
        
        // Check required
        if (rules.required && !value) {
            showError(field, 'This field is required.');
            return false;
        }
        
        if (!value) return true;
        
        // Check pattern
        if (rules.pattern && !rules.pattern.test(value)) {
            showError(field, rules.message);
            return false;
        }
        
        // Check min length
        if (rules.minLength && value.length < rules.minLength) {
            showError(field, `Must be at least ${rules.minLength} characters.`);
            return false;
        }
        
        // Check max length
        if (rules.maxLength && value.length > rules.maxLength) {
            showError(field, `Must be at most ${rules.maxLength} characters.`);
            return false;
        }
        
        // Check min value
        if (rules.min !== undefined && parseFloat(value) < rules.min) {
            showError(field, `Must be at least ${rules.min}.`);
            return false;
        }
        
        clearError(field);
        return true;
    }
    
    function showError(field, message) {
        clearError(field);
        field.classList.add('is-invalid');
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        field.parentNode.appendChild(feedback);
    }
    
    function clearError(field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) feedback.remove();
    }
    
    // Attach validation to all form fields
    document.addEventListener('DOMContentLoaded', function() {
        const forms = document.querySelectorAll('[data-validate="true"]');
        
        forms.forEach(form => {
            const fields = form.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], input[type="number"], input[type="url"], textarea, select');
            
            fields.forEach(field => {
                // Validate on blur
                field.addEventListener('blur', function() {
                    validateField(this);
                });
                
                // Validate on input (for real-time feedback)
                field.addEventListener('input', function() {
                    if (this.classList.contains('is-invalid')) {
                        validateField(this);
                    }
                });
            });
            
            // Validate on form submit
            form.addEventListener('submit', function(e) {
                let isValid = true;
                const fields = this.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], input[type="number"], input[type="url"], textarea, select');
                
                fields.forEach(field => {
                    if (!validateField(field)) {
                        isValid = false;
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            });
        });
    });
})();
</script>
"""
