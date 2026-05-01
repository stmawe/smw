"""Authentication views for UniMarket."""

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


@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    Tenant-aware user registration view.
    Registers user in the current tenant's schema.
    """
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role', 'buyer')
        
        # Validation
        if not email or not password1 or not password2:
            messages.error(request, 'All fields are required.')
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
        
        # Create user
        try:
            user = User.objects.create_user(
                email=email,
                username=email,  # Use email as username
                password=password1,
                role=role
            )
            user.is_active = False  # Require email verification
            user.save()
            
            # Create email address record
            EmailAddress.objects.create(
                user=user,
                email=email,
                verified=False,
                primary=True
            )
            
            messages.success(request, 'Registration successful. Please check your email to verify your account.')
            return redirect('accounts:login')
        
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return redirect('register')
    
    return render(request, 'accounts/register.html')


@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Tenant-aware login view.
    """
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return redirect('accounts:login')
        
        # Authenticate with email
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            
            if user is not None:
                if not user.is_active:
                    messages.error(request, 'Please verify your email before logging in.')
                    return redirect('accounts:login')
                
                login(request, user)
                messages.success(request, f'Welcome back, {user.email}!')
                return redirect('/')
            else:
                messages.error(request, 'Invalid email or password.')
                return redirect('accounts:login')
        
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
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
