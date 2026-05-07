"""
Admin views for managing shop managers and moderators.
Accessible at admin.smw.pgwiz.cloud/admin/team/
"""

import logging
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from app.models import User
from app.admin_views import admin_login_required

logger = logging.getLogger(__name__)


@admin_login_required
@require_http_methods(['GET'])
def team_list_view(request):
    """
    List all users with elevated roles (shop_manager, moderator, entity admins).
    GET /admin/team/
    """
    role_filter = request.GET.get('role', 'all')

    users = User.objects.exclude(role__in=['buyer', 'seller']).order_by('role', 'username')
    if role_filter != 'all':
        users = users.filter(role=role_filter)

    role_counts = {
        'superadmin': User.objects.filter(role='superadmin').count(),
        'university_admin': User.objects.filter(role='university_admin').count(),
        'area_admin': User.objects.filter(role='area_admin').count(),
        'shop_manager': User.objects.filter(role='shop_manager').count(),
        'moderator': User.objects.filter(role='moderator').count(),
    }

    return render(request, 'admin/team.html', {
        'users': users,
        'role_filter': role_filter,
        'role_counts': role_counts,
        'page_title': 'Team Management',
    })


@admin_login_required
@require_http_methods(['GET', 'POST'])
def assign_role_view(request, user_id):
    """
    Assign or change a user's role.
    GET/POST /admin/team/{user_id}/role/
    """
    user = get_object_or_404(User, pk=user_id)

    ASSIGNABLE_ROLES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('shop_manager', 'Shop Manager'),
        ('moderator', 'Moderator'),
        ('university_admin', 'University Admin'),
        ('area_admin', 'Area Admin'),
    ]

    if request.method == 'POST':
        new_role = request.POST.get('role', '').strip()
        valid_roles = [r[0] for r in ASSIGNABLE_ROLES]
        if new_role not in valid_roles:
            messages.error(request, f'Invalid role: {new_role}')
        else:
            old_role = user.role
            user.role = new_role
            user.save(update_fields=['role'])
            messages.success(request, f'{user.username} role changed: {old_role} → {new_role}')
            logger.info('Role change: %s → %s for user %s by %s', old_role, new_role, user.username, request.user.username)
        return redirect('admin_team_list')

    return render(request, 'admin/assign_role.html', {
        'target_user': user,
        'assignable_roles': ASSIGNABLE_ROLES,
        'page_title': f'Assign Role — {user.username}',
    })


@admin_login_required
@require_http_methods(['GET'])
def shop_managers_list_view(request):
    """
    List all ShopManager assignments across all tenant schemas.
    GET /admin/team/shop-managers/
    """
    from django_tenants.utils import schema_context
    from app.models import Client

    assignments = []
    tenants = Client.objects.exclude(schema_name='public').order_by('name')

    for tenant in tenants:
        try:
            with schema_context(tenant.schema_name):
                from mydak.models import ShopManager
                mgrs = list(
                    ShopManager.objects.filter(is_active=True)
                    .select_related('shop', 'manager', 'assigned_by')
                    .order_by('shop__name')
                )
                for m in mgrs:
                    assignments.append({
                        'schema': tenant.schema_name,
                        'tenant_name': tenant.name,
                        'shop_name': m.shop.name,
                        'shop_id': m.shop.id,
                        'manager_username': m.manager.username,
                        'manager_email': m.manager.email,
                        'can_edit_listings': m.can_edit_listings,
                        'can_view_orders': m.can_view_orders,
                        'can_message_buyers': m.can_message_buyers,
                        'assignment_id': m.id,
                    })
        except Exception:
            continue

    return render(request, 'admin/shop_managers.html', {
        'assignments': assignments,
        'total': len(assignments),
        'page_title': 'Shop Managers',
    })


@admin_login_required
@require_http_methods(['POST'])
def assign_shop_manager_view(request):
    """
    Assign a user as manager of a shop.
    POST /admin/team/shop-managers/assign/
    Requires: shop_id, manager_username, schema, permissions
    """
    from django_tenants.utils import schema_context

    schema = request.POST.get('schema', '').strip()
    shop_id = request.POST.get('shop_id', '').strip()
    manager_username = request.POST.get('manager_username', '').strip()

    if not schema or not shop_id or not manager_username:
        messages.error(request, 'Schema, shop ID, and manager username are required.')
        return redirect('admin_shop_managers')

    try:
        manager = User.objects.get(username=manager_username)
    except User.DoesNotExist:
        messages.error(request, f'User "{manager_username}" not found.')
        return redirect('admin_shop_managers')

    try:
        with schema_context(schema):
            from mydak.models import Shop, ShopManager
            shop = get_object_or_404(Shop, pk=shop_id)
            assignment, created = ShopManager.objects.get_or_create(
                shop=shop,
                manager=manager,
                defaults={
                    'assigned_by': request.user,
                    'can_edit_listings': bool(request.POST.get('can_edit_listings')),
                    'can_view_orders': bool(request.POST.get('can_view_orders')),
                    'can_message_buyers': bool(request.POST.get('can_message_buyers')),
                    'is_active': True,
                }
            )
            if not created:
                assignment.can_edit_listings = bool(request.POST.get('can_edit_listings'))
                assignment.can_view_orders = bool(request.POST.get('can_view_orders'))
                assignment.can_message_buyers = bool(request.POST.get('can_message_buyers'))
                assignment.is_active = True
                assignment.save()

            # Also set the user's role to shop_manager if not already elevated
            if manager.role in ('buyer', 'seller'):
                manager.role = 'shop_manager'
                manager.save(update_fields=['role'])

            action = 'assigned' if created else 'updated'
            messages.success(request, f'{manager_username} {action} as manager of "{shop.name}".')
    except Exception as exc:
        messages.error(request, f'Assignment failed: {exc}')

    return redirect('admin_shop_managers')


@admin_login_required
@require_http_methods(['POST'])
def revoke_shop_manager_view(request, assignment_id):
    """
    Revoke a shop manager assignment.
    POST /admin/team/shop-managers/{assignment_id}/revoke/
    """
    from django_tenants.utils import schema_context

    schema = request.POST.get('schema', '').strip()
    if not schema:
        messages.error(request, 'Schema is required.')
        return redirect('admin_shop_managers')

    try:
        with schema_context(schema):
            from mydak.models import ShopManager
            assignment = get_object_or_404(ShopManager, pk=assignment_id)
            username = assignment.manager.username
            shop_name = assignment.shop.name
            assignment.is_active = False
            assignment.save(update_fields=['is_active', 'updated_at'])
            messages.success(request, f'Revoked {username} as manager of "{shop_name}".')
    except Exception as exc:
        messages.error(request, f'Revoke failed: {exc}')

    return redirect('admin_shop_managers')
