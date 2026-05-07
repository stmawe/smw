"""Authentication views for UniMarket."""

import logging

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from allauth.account.views import SignupView
from allauth.account.models import EmailAddress

User = get_user_model()
logger = logging.getLogger(__name__)


def _register_user_subdomain(username: str) -> None:
    """
    Create a Cloudflare DNS A record for {username}.smw.pgwiz.cloud on user registration.
    Delegates to the shared helper in app/cloudflare_dns.py.
    Non-fatal — logs errors but never raises.
    """
    from app.cloudflare_dns import create_subdomain_dns_record
    create_subdomain_dns_record(username)


def _issue_user_ssl(username: str) -> None:
    """
    Issue a Let's Encrypt SSL certificate for {username}.smw.pgwiz.cloud
    using the Serv00 devil command.

    Must be called AFTER the Cloudflare DNS A record is created.
    Non-fatal — logs errors but never raises.
    """
    import subprocess
    from django.conf import settings

    base_domain = getattr(settings, 'BASE_DOMAIN', 'smw.pgwiz.cloud')
    if 'localhost' in base_domain:
        logger.info('SSL skipped for %s — localhost environment', username)
        return

    subdomain = f'{username}.{base_domain}'
    server_ip = getattr(settings, 'SERVER_IP', '128.204.223.70')

    try:
        result = subprocess.run(
            ['devil', 'ssl', 'www', 'add', server_ip, 'le', 'le', subdomain],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            logger.info('SSL cert issued for %s', subdomain)
        else:
            logger.error('devil ssl failed for %s: %s', subdomain, result.stderr or result.stdout)
    except Exception as exc:
        logger.error('SSL issuance failed for %s: %s', subdomain, exc)


@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    Tenant-aware user registration view.
    Registers user in the current tenant's schema.
    """
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        import re
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip().lower()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', 'buyer')

        # Validation
        if not email or not username or not password1 or not password2:
            messages.error(request, 'All fields are required.')
            return redirect('register')

        # Username: lowercase letters, digits, hyphens only — no dots (subdomain safety)
        if not re.match(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$', username) and not re.match(r'^[a-z0-9]$', username):
            messages.error(request, 'Username may only contain lowercase letters, digits, and hyphens. No dots or spaces.')
            return redirect('register')

        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters.')
            return redirect('register')

        if len(username) > 48:
            messages.error(request, 'Username must be 48 characters or less.')
            return redirect('register')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')

        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'That username is already taken.')
            return redirect('register')

        # Create user
        try:
            user = User.objects.create_user(
                email=email,
                username=username,
                password=password1,
                role=role,
            )
            user.is_active = False  # Require email verification
            user.save()

            # Register the user's personal subdomain with Cloudflare (non-fatal)
            _register_user_subdomain(user.username)

            # Issue SSL certificate for the user's subdomain via devil (non-fatal)
            _issue_user_ssl(user.username)

            # Create email address record
            EmailAddress.objects.create(
                user=user,
                email=email,
                verified=False,
                primary=True,
            )

            messages.success(request, 'Registration successful. Please check your email to verify your account.')
            return render(request, 'accounts/setup_pending.html', {
                'username': user.username,
            })

        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return redirect('register')
    
    return render(request, 'accounts/register.html')


@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Tenant-aware login view.
    Accepts username OR email — delegates to UsernameOrEmailBackend.
    """
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        # Accept either 'email' or 'username' field name from the form
        identifier = (
            request.POST.get('email') or
            request.POST.get('username') or
            ''
        ).strip()
        password = request.POST.get('password', '').strip()

        if not identifier or not password:
            messages.error(request, 'Username/email and password are required.')
            return redirect('accounts:login')

        # UsernameOrEmailBackend handles both username and email lookup
        user = authenticate(request, username=identifier, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, 'This account is not active. Please verify your email.')
                return redirect('accounts:login')
            login(request, user)
            # Redirect to user's personal dashboard after login
            next_url = request.GET.get('next', '')
            if not next_url:
                from django.conf import settings as django_settings
                base_domain = getattr(django_settings, 'BASE_DOMAIN', 'smw.pgwiz.cloud')
                if 'localhost' in base_domain or '127.0.0.1' in base_domain:
                    base_domain = 'smw.pgwiz.cloud'
                protocol = 'http' if django_settings.DEBUG else 'https'
                next_url = f'{protocol}://{user.username}.{base_domain}/dashboard/'
            messages.success(request, f'Welcome back, {user.email}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username/email or password.')
            return redirect('accounts:login')

    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """
    Logout view.
    """
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('/')


@login_required
def profile_view(request):
    """
    User profile view.
    """
    user = request.user
    context = {
        'user': user,
        'email_verified': user.emailaddress_set.filter(primary=True, verified=True).exists()
    }
    return render(request, 'accounts/profile.html', context)


@login_required
@require_http_methods(["POST"])
def profile_edit_view(request):
    """
    Edit user profile (AJAX endpoint).
    """
    user = request.user
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    
    user.save()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Profile updated successfully.',
        'user': {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        }
    })


@login_required
@require_http_methods(["POST"])
def change_password_view(request):
    """
    Change password view (AJAX endpoint).
    """
    user = request.user
    old_password = request.POST.get('old_password', '')
    new_password1 = request.POST.get('new_password1', '')
    new_password2 = request.POST.get('new_password2', '')
    
    if not old_password or not new_password1 or not new_password2:
        return JsonResponse({'status': 'error', 'message': 'All fields are required.'}, status=400)
    
    if new_password1 != new_password2:
        return JsonResponse({'status': 'error', 'message': 'Passwords do not match.'}, status=400)
    
    if not user.check_password(old_password):
        return JsonResponse({'status': 'error', 'message': 'Old password is incorrect.'}, status=400)
    
    user.set_password(new_password1)
    user.save()
    
    # Re-authenticate user to keep them logged in
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    
    return JsonResponse({
        'status': 'success',
        'message': 'Password changed successfully.'
    })


def verify_email_view(request, key):
    """
    Verify email address (handles allauth confirmation emails).
    This is handled by allauth, but we can extend it if needed.
    """
    # allauth handles this automatically via its email confirmation flow
    from allauth.account.views import ConfirmEmailView
    return ConfirmEmailView.as_view()(request, key=key)
