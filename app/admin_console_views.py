"""
Admin console view for managing domains and SSL certificates
Accessible at: https://admin.smw.pgwiz.cloud/console/domains/
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from mydak.models import Shop
from .admin_views import admin_login_required
from .admin_permissions import permission_required, AdminPermission
import subprocess
import json


def is_staff(user):
    """Check if user is staff/admin"""
    return user.is_staff or user.is_superuser


@admin_login_required
@permission_required(AdminPermission.MANAGE_SHOP_DOMAINS)
def domains_console_view(request):
    """
    Admin console for managing domains and SSL certificates.
    Shows all shops with their domains and SSL status.
    Requires: admin:manage_shop_domains permission
    """
    shops = Shop.objects.select_related('owner').all().order_by('-created_at')
    
    # Get SSL status for each shop
    shops_with_ssl = []
    for shop in shops:
        domain = f'{shop.slug}.smw.pgwiz.cloud'
        ssl_status = _get_ssl_status(domain)
        
        shops_with_ssl.append({
            'shop': shop,
            'domain': domain,
            'ssl_status': ssl_status,
            'needs_ssl': not ssl_status['has_ssl']
        })
    
    context = {
        'shops': shops_with_ssl,
        'total_shops': shops.count(),
        'ssl_configured': sum(1 for s in shops_with_ssl if s['ssl_status']['has_ssl']),
    }
    
    return render(request, 'admin/console_domains.html', context)


@admin_login_required
@permission_required(AdminPermission.MANAGE_SHOP_DOMAINS)
@require_http_methods(['POST'])
def add_ssl_for_shop_view(request, shop_id):
    """
    AJAX endpoint to add SSL certificate for a shop
    POST: shop_id
    Returns: JSON with status
    Requires: admin:manage_shop_domains permission
    """
    try:
        shop = get_object_or_404(Shop, id=shop_id)
        domain = f'{shop.slug}.smw.pgwiz.cloud'
        
        # Generate SSL
        result = _generate_ssl_for_domain(domain)
        
        if result['success']:
            messages.success(request, f'SSL certificate generated for {domain}')
            return JsonResponse({
                'success': True,
                'message': f'SSL certificate generated for {domain}',
                'domain': domain
            })
        else:
            error_msg = result.get('error', 'Unknown error')
            return JsonResponse({
                'success': False,
                'message': f'Failed to generate SSL: {error_msg}',
                'domain': domain
            }, status=400)
    
    except Shop.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Shop not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@admin_login_required
@permission_required(AdminPermission.MANAGE_SHOP_DOMAINS)
def ssl_status_view(request, shop_id):
    """
    AJAX endpoint to check SSL status for a shop
    GET: shop_id
    Returns: JSON with SSL status
    Requires: admin:manage_shop_domains permission
    """
    try:
        shop = get_object_or_404(Shop, id=shop_id)
        domain = f'{shop.slug}.smw.pgwiz.cloud'
        
        status = _get_ssl_status(domain)
        
        return JsonResponse({
            'domain': domain,
            'has_ssl': status['has_ssl'],
            'expires': status.get('expires'),
            'issued': status.get('issued'),
        })
    
    except Shop.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Shop not found'}, status=404)


def _generate_ssl_for_domain(domain):
    """
    Generate SSL certificate for domain using devil ssl command.
    
    Returns:
        dict with 'success' bool and 'error' if failed
    """
    ip_address = '128.204.223.70'
    
    try:
        cmd = f'devil ssl www add {ip_address} le le {domain}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 or 'Certificate added' in result.stdout or 'successfully' in result.stdout.lower():
            return {'success': True}
        elif 'already being used' in result.stdout or 'already' in result.stdout.lower():
            return {'success': True, 'message': 'Certificate already exists'}
        else:
            return {'success': False, 'error': result.stderr or result.stdout}
    
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Certificate generation timed out'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _get_ssl_status(domain):
    """
    Check SSL certificate status for domain.
    
    Returns:
        dict with SSL status information
    """
    try:
        # Use devil ssl command to check
        cmd = f'devil ssl www list'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if domain.lower() in result.stdout.lower():
            # Parse output to get expiration date
            lines = result.stdout.split('\n')
            for line in lines:
                if domain.lower() in line.lower():
                    parts = line.split()
                    return {
                        'has_ssl': True,
                        'domain': domain,
                        'issued': parts[1] if len(parts) > 1 else 'Unknown',
                        'expires': parts[2] if len(parts) > 2 else 'Unknown',
                    }
            
            return {'has_ssl': True, 'domain': domain}
        else:
            return {'has_ssl': False, 'domain': domain}
    
    except Exception as e:
        return {'has_ssl': False, 'domain': domain, 'error': str(e)}



@admin_login_required
def user_domains_console_view(request):
    """
    Admin console for managing user subdomains and their SSL certificates.
    Accessible at: admin.smw.pgwiz.cloud/console/user-domains/
    Shows all ClientDomain records (user subdomains) with SSL status.
    """
    from app.models import ClientDomain, User
    from django.conf import settings

    base_domain = getattr(settings, 'BASE_DOMAIN', 'smw.pgwiz.cloud')
    server_ip = getattr(settings, 'SERVER_IP', '128.204.223.70')

    # Get all user subdomains (exclude public and admin)
    excluded = {'smw.pgwiz.cloud', 'admin.smw.pgwiz.cloud', 'localhost'}
    client_domains = ClientDomain.objects.select_related('tenant').exclude(
        domain__in=excluded
    ).order_by('domain')

    # Get current SSL certs from devil
    ssl_domains = set()
    try:
        result = subprocess.run(
            ['devil', 'ssl', 'www', 'list'],
            capture_output=True, text=True, timeout=15
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if parts and '.' in parts[0] and not parts[0].startswith('Common'):
                ssl_domains.add(parts[0].strip())
    except Exception:
        pass

    domains_data = []
    for cd in client_domains:
        username = cd.domain.replace(f'.{base_domain}', '') if cd.domain.endswith(f'.{base_domain}') else cd.domain
        has_ssl = cd.domain in ssl_domains
        try:
            user = User.objects.get(username=username)
            user_email = user.email
            user_active = user.is_active
        except User.DoesNotExist:
            user_email = ''
            user_active = False

        domains_data.append({
            'domain': cd.domain,
            'username': username,
            'schema': cd.tenant.schema_name,
            'has_ssl': has_ssl,
            'user_email': user_email,
            'user_active': user_active,
        })

    return render(request, 'admin/user_domains.html', {
        'domains': domains_data,
        'total': len(domains_data),
        'ssl_count': sum(1 for d in domains_data if d['has_ssl']),
        'server_ip': server_ip,
        'page_title': 'User Domains',
    })


@admin_login_required
@require_http_methods(['POST'])
def issue_ssl_for_user_view(request, username):
    """
    Issue SSL cert for a user subdomain via devil ssl www add.
    POST /console/user-domains/{username}/ssl/
    """
    from django.conf import settings

    base_domain = getattr(settings, 'BASE_DOMAIN', 'smw.pgwiz.cloud')
    server_ip = getattr(settings, 'SERVER_IP', '128.204.223.70')
    subdomain = f'{username}.{base_domain}'

    try:
        result = subprocess.run(
            ['devil', 'ssl', 'www', 'add', server_ip, 'le', 'le', subdomain],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            messages.success(request, f'SSL certificate issued for {subdomain}')
        else:
            messages.error(request, f'SSL failed for {subdomain}: {result.stderr or result.stdout}')
    except Exception as exc:
        messages.error(request, f'SSL error for {subdomain}: {exc}')

    return redirect('admin_user_domains')
