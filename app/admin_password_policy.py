"""
Password policy enforcement for admin users.
Enforces strong password requirements for all admin accounts.
"""

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.validators import MinimumLengthValidator, CommonPasswordValidator
from django.utils.translation import gettext_lazy as _
import re


class AdminPasswordValidator:
    """Validator for enforcing strong admin passwords."""
    
    MIN_LENGTH = 12
    
    def __init__(self):
        self.min_length_validator = MinimumLengthValidator(self.MIN_LENGTH)
        self.common_password_validator = CommonPasswordValidator()
    
    def validate(self, password, user=None):
        """Validate password against admin requirements."""
        # Check minimum length
        self.min_length_validator.validate(password, user)
        
        # Check for common passwords
        self.common_password_validator.validate(password, user)
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='no_uppercase',
            )
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code='no_lowercase',
            )
        
        # Check for digit
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code='no_digit',
            )
        
        # Check for special character
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/`~\\|]', password):
            raise ValidationError(
                _("Password must contain at least one special character (!@#$%^&*()_+-=[]{};:'\",.<>?/`~\\|)."),
                code='no_special_char',
            )
    
    def get_help_text(self):
        """Return help text for password requirements."""
        return _("Password must be at least 12 characters and contain uppercase, lowercase, digit, and special character.")


class AdminPasswordPolicyMiddleware:
    """
    Middleware to enforce password policy for admin users.
    Checks password age and forces password reset if needed.
    """
    
    PASSWORD_EXPIRY_DAYS = 90  # Force password change every 90 days
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if user is admin and password needs update
        if request.user.is_authenticated and request.user.is_staff:
            if self.should_force_password_change(request):
                from django.shortcuts import redirect
                return redirect('admin_change_password')
        
        response = self.get_response(request)
        return response
    
    @staticmethod
    def should_force_password_change(request):
        """Check if user password needs to be changed."""
        if not hasattr(request.user, 'last_password_change'):
            return False
        
        from datetime import datetime, timedelta
        
        last_change = request.user.last_password_change
        if not last_change:
            return True
        
        days_since_change = (datetime.now() - last_change).days
        return days_since_change > AdminPasswordPolicyMiddleware.PASSWORD_EXPIRY_DAYS


class PasswordPolicyForm:
    """Utility for password policy form fields and validation."""
    
    @staticmethod
    def get_password_field_help_text():
        """Return help text for password field."""
        return (
            "Password must contain at least 12 characters, including "
            "uppercase, lowercase, digits, and special characters (!@#$%^&*()_+-=[]{};:'\",.<>?/`~\\|)"
        )
    
    @staticmethod
    def get_password_requirements_html():
        """Return HTML for password requirements display."""
        return """
        <div class="alert alert-info" role="alert">
            <strong>Password Requirements:</strong>
            <ul class="mb-0">
                <li>Minimum 12 characters</li>
                <li>At least one uppercase letter (A-Z)</li>
                <li>At least one lowercase letter (a-z)</li>
                <li>At least one digit (0-9)</li>
                <li>At least one special character (!@#$%^&*()_+-=[]{};:'",.&lt;&gt;?/`~\\|)</li>
            </ul>
        </div>
        """
    
    @staticmethod
    def get_password_strength_js():
        """Return JavaScript for real-time password strength checking."""
        return """
        <script>
        (function() {
            const passwordInput = document.getElementById('id_password') || document.getElementById('password');
            if (!passwordInput) return;
            
            const requirements = {
                'length': false,      // >= 12 chars
                'uppercase': false,   // A-Z
                'lowercase': false,   // a-z
                'digit': false,       // 0-9
                'special': false      // Special char
            };
            
            function checkPassword(password) {
                requirements.length = password.length >= 12;
                requirements.uppercase = /[A-Z]/.test(password);
                requirements.lowercase = /[a-z]/.test(password);
                requirements.digit = /\\d/.test(password);
                requirements.special = /[!@#$%^&*()_+\\-=\\[\\]{};:'",.<>?/`~\\|]/.test(password);
                
                updateDisplay();
            }
            
            function updateDisplay() {
                // Update requirement indicators
                document.querySelectorAll('[data-requirement]').forEach(elem => {
                    const req = elem.getAttribute('data-requirement');
                    if (requirements[req]) {
                        elem.classList.add('valid');
                        elem.classList.remove('invalid');
                    } else {
                        elem.classList.add('invalid');
                        elem.classList.remove('valid');
                    }
                });
                
                // Update strength meter
                const strength = Object.values(requirements).filter(v => v).length;
                const strengthMeter = document.getElementById('password-strength');
                if (strengthMeter) {
                    strengthMeter.style.width = (strength * 20) + '%';
                    strengthMeter.className = 'progress-bar';
                    if (strength < 3) strengthMeter.classList.add('bg-danger');
                    else if (strength < 5) strengthMeter.classList.add('bg-warning');
                    else strengthMeter.classList.add('bg-success');
                }
            }
            
            passwordInput.addEventListener('input', function() {
                checkPassword(this.value);
            });
            
            // Initial check
            checkPassword(passwordInput.value);
        })();
        </script>
        """


def validate_admin_password(password, user=None):
    """Validate password for admin users."""
    validator = AdminPasswordValidator()
    validator.validate(password, user)
