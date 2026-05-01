"""
Admin changelog view with detailed change history and filtering.
"""

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from app.models import AdminAuditLog
from app.admin_utils import permission_required
from app.admin_permissions import AdminPermission
from app.admin_pagination import OptimizedPaginator


@require_http_methods(["GET"])
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
def changelog_view(request):
    """View detailed changelog of system changes."""
    
    # Get filters
    resource_type = request.GET.get('resource_type', '')
    action = request.GET.get('action', '')
    admin = request.GET.get('admin', '')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '').strip()
    
    # Base queryset
    logs = AdminAuditLog.objects.select_related('admin').order_by('-created_at')
    
    # Apply filters
    if resource_type:
        logs = logs.filter(resource_type=resource_type)
    
    if action:
        logs = logs.filter(action__icontains=action)
    
    if admin:
        logs = logs.filter(admin__username__icontains=admin)
    
    if status_filter:
        logs = logs.filter(status=status_filter)
    
    if search:
        logs = logs.filter(
            Q(admin__username__icontains=search) |
            Q(action__icontains=search) |
            Q(resource_type__icontains=search) |
            Q(details__icontains=search)
        )
    
    # Get unique values for filters
    resource_types = AdminAuditLog.objects.values_list('resource_type', flat=True).distinct()
    actions = AdminAuditLog.objects.values_list('action', flat=True).distinct()
    admins = AdminAuditLog.objects.filter(admin__isnull=False).values_list('admin__username', flat=True).distinct()
    
    # Paginate
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 50)
    page_obj = OptimizedPaginator.get_paginated_queryset(logs, page, per_page)
    
    context = {
        'page': page_obj,
        'resource_types': sorted(set(resource_types)),
        'actions': sorted(set(actions)),
        'admins': sorted(set(admins)),
        'filters': {
            'resource_type': resource_type,
            'action': action,
            'admin': admin,
            'status': status_filter,
            'search': search,
        },
        'title': 'Changelog',
    }
    
    return render(request, 'admin/changelog.html', context)


@require_http_methods(["GET"])
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
def changelog_detail(request, log_id):
    """View detailed change information."""
    from django.shortcuts import get_object_or_404
    
    log = get_object_or_404(AdminAuditLog, id=log_id)
    
    # Parse before/after values
    before = log.before if isinstance(log.before, dict) else {}
    after = log.after if isinstance(log.after, dict) else {}
    
    # Calculate diffs
    all_keys = set(before.keys()) | set(after.keys())
    changes = {}
    
    for key in all_keys:
        old_val = before.get(key)
        new_val = after.get(key)
        
        if old_val != new_val:
            changes[key] = {
                'old': old_val,
                'new': new_val,
                'changed': True
            }
        else:
            changes[key] = {
                'old': old_val,
                'new': new_val,
                'changed': False
            }
    
    context = {
        'log': log,
        'changes': changes,
        'title': f'Change Details: {log.action}',
    }
    
    return render(request, 'admin/changelog_detail.html', context)
