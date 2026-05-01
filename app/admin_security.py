"""
Two-factor authentication (2FA) for admin users.
Supports TOTP (Time-based One-Time Password) authentication.
"""

import pyotp
import qrcode
import io
import base64
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User


class AdminTwoFactorAuth:
    """Two-factor authentication service for admin users."""
    
    @staticmethod
    def generate_secret():
        """Generate a new TOTP secret."""
        return pyotp.random_base32()
    
    @staticmethod
    def get_totp(secret):
        """Get TOTP object from secret."""
        return pyotp.TOTP(secret)
    
    @staticmethod
    def verify_token(secret, token):
        """Verify TOTP token."""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token)
        except Exception:
            return False
    
    @staticmethod
    def generate_qr_code(user, secret):
        """Generate QR code for 2FA setup."""
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user.email,
            issuer_name='Admin Panel'
        )
        
        qr = qrcode.QRCode()
        qr.add_data(uri)
        qr.make()
        
        img = qr.make_image()
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"


class IPWhitelistService:
    """IP whitelist service for admin access control."""
    
    @staticmethod
    def is_ip_allowed(ip_address, whitelist):
        """Check if IP is in whitelist."""
        if not whitelist:
            return True
        
        for ip_pattern in whitelist:
            if AdminTwoFactorAuth._match_ip(ip_address, ip_pattern):
                return True
        
        return False
    
    @staticmethod
    def _match_ip(ip_address, pattern):
        """Check if IP matches pattern (supports CIDR and exact match)."""
        if '/' in pattern:
            # CIDR notation
            import ipaddress
            try:
                network = ipaddress.ip_network(pattern, strict=False)
                ip = ipaddress.ip_address(ip_address)
                return ip in network
            except Exception:
                return False
        else:
            # Exact match
            return ip_address == pattern
    
    @staticmethod
    def add_ip_to_whitelist(user, ip_address):
        """Add IP to user's whitelist."""
        whitelist = getattr(user, 'ip_whitelist', []) or []
        if ip_address not in whitelist:
            whitelist.append(ip_address)
            user.ip_whitelist = whitelist
            user.save()
    
    @staticmethod
    def remove_ip_from_whitelist(user, ip_address):
        """Remove IP from user's whitelist."""
        whitelist = getattr(user, 'ip_whitelist', []) or []
        if ip_address in whitelist:
            whitelist.remove(ip_address)
            user.ip_whitelist = whitelist
            user.save()


class SessionTimeoutService:
    """Session timeout management for admin users."""
    
    ADMIN_SESSION_TIMEOUT = 30 * 60  # 30 minutes
    VIEWER_SESSION_TIMEOUT = 60 * 60  # 60 minutes
    
    @staticmethod
    def get_session_timeout(user):
        """Get session timeout for user based on role."""
        if user.is_superuser:
            return SessionTimeoutService.ADMIN_SESSION_TIMEOUT
        elif user.is_staff:
            return SessionTimeoutService.ADMIN_SESSION_TIMEOUT
        else:
            return SessionTimeoutService.VIEWER_SESSION_TIMEOUT
    
    @staticmethod
    def get_remaining_time(request):
        """Get remaining session time in seconds."""
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        
        try:
            session = Session.objects.get(session_key=request.session.session_key)
            expiry = session.expire_date
            remaining = (expiry - timezone.now()).total_seconds()
            return max(0, int(remaining))
        except Exception:
            return 0


def setup_2fa(request):
    """Setup 2FA for user."""
    user = request.user
    
    if request.method == 'GET':
        # Generate new secret
        secret = AdminTwoFactorAuth.generate_secret()
        qr_code = AdminTwoFactorAuth.generate_qr_code(user, secret)
        
        # Store in session temporarily
        request.session['2fa_setup_secret'] = secret
        
        context = {
            'secret': secret,
            'qr_code': qr_code,
            'backup_codes': [f"{i:06d}" for i in range(10)],  # Generate 10 backup codes
        }
        
        return render(request, 'admin/security/2fa_setup.html', context)
    
    elif request.method == 'POST':
        # Verify token
        token = request.POST.get('token')
        secret = request.session.get('2fa_setup_secret')
        
        if AdminTwoFactorAuth.verify_token(secret, token):
            # Save 2FA secret
            user.two_factor_secret = secret
            user.two_factor_enabled = True
            user.save()
            
            # Clear session
            del request.session['2fa_setup_secret']
            
            return redirect('admin_dashboard')
        else:
            return render(request, 'admin/security/2fa_setup.html', {
                'error': 'Invalid token. Please try again.'
            })


def verify_2fa(request):
    """Verify 2FA token on login."""
    if request.method == 'POST':
        token = request.POST.get('token')
        user_id = request.session.get('2fa_user_id')
        
        try:
            user = User.objects.get(id=user_id)
            secret = user.two_factor_secret
            
            if AdminTwoFactorAuth.verify_token(secret, token):
                # Token valid, complete login
                from django.contrib.auth import login
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('admin_dashboard')
            else:
                return render(request, 'admin/security/2fa_verify.html', {
                    'error': 'Invalid token. Please try again.'
                })
        except User.DoesNotExist:
            return render(request, 'admin/security/2fa_verify.html', {
                'error': 'User not found.'
            })
    
    return render(request, 'admin/security/2fa_verify.html')


def disable_2fa(request):
    """Disable 2FA for user."""
    if request.method == 'POST':
        password = request.POST.get('password')
        
        # Verify password
        if request.user.check_password(password):
            request.user.two_factor_enabled = False
            request.user.two_factor_secret = None
            request.user.save()
            
            return redirect('admin_settings')
        else:
            return render(request, 'admin/security/disable_2fa.html', {
                'error': 'Invalid password.'
            })
    
    return render(request, 'admin/security/disable_2fa.html')


@require_http_methods(["GET"])
def check_session_timeout(request):
    """API endpoint to check session timeout."""
    remaining = SessionTimeoutService.get_remaining_time(request)
    
    return JsonResponse({
        'remaining_seconds': remaining,
        'will_expire_soon': remaining < 5 * 60,  # Warning at 5 minutes
    })


def extend_session(request):
    """Extend user session."""
    request.session.set_expiry(SessionTimeoutService.get_session_timeout(request.user))
    
    return JsonResponse({
        'success': True,
        'message': 'Session extended.',
    })
