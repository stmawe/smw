"""
Entity admin views — manage institutions (universities, locations, etc.)
at admin.smw.pgwiz.cloud/admin/entities/

All views require admin login (staff or superuser).
State-changing views (approve, reject, suspend, reactivate) are POST-only.
"""

import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from app.cloudflare_dns import create_subdomain_dns_record
from app.forms import EntityAdminForm
from app.models import Entity

logger = logging.getLogger(__name__)


def _admin_login_required(view_func):
    """Import and apply the admin_login_required decorator from admin_views."""
    from app.admin_views import admin_login_required
    return admin_login_required(view_func)


@_admin_login_required
@require_http_methods(['GET'])
def entity_list_view(request):
    """
    List all entities with optional status filter.
    GET /admin/entities/?status=pending|active|suspended|all
    """
    status_filter = request.GET.get('status', 'all')
    entities = Entity.objects.all().order_by('name')

    if status_filter in ('pending', 'active', 'suspended'):
        entities = entities.filter(status=status_filter)

    counts = {
        'all':       Entity.objects.count(),
        'pending':   Entity.objects.filter(status='pending').count(),
        'active':    Entity.objects.filter(status='active').count(),
        'suspended': Entity.objects.filter(status='suspended').count(),
    }

    return render(request, 'admin/entities.html', {
        'entities': entities,
        'status_filter': status_filter,
        'counts': counts,
        'page_title': 'Entities',
    })


@_admin_login_required
@require_http_methods(['GET', 'POST'])
def entity_create_view(request):
    """
    Create a new entity (admin-created path — immediately active).
    GET/POST /admin/entities/create/
    """
    if request.method == 'POST':
        form = EntityAdminForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            entity = Entity(
                name=data['name'],
                entity_type=data['entity_type'],
                subdomain=data['subdomain'],
                admin_user=data.get('admin_user'),
                status='active',          # admin-created = immediately active
                city=data.get('city', ''),
                country=data.get('country', ''),
                website=data.get('website', ''),
                created_by=request.user,
            )
            entity.save()  # save() syncs is_active=True

            # Register Cloudflare DNS (non-fatal)
            try:
                create_subdomain_dns_record(entity.subdomain)
            except Exception as exc:
                logger.error('DNS registration failed for entity %s: %s', entity.subdomain, exc)

            messages.success(request, f'Entity "{entity.name}" created and activated.')
            return redirect('admin_entities_list')
    else:
        form = EntityAdminForm(initial={'status': 'active'})

    return render(request, 'admin/entity_form.html', {
        'form': form,
        'action': 'Create',
        'page_title': 'Create Entity',
    })


@_admin_login_required
@require_http_methods(['GET', 'POST'])
def entity_edit_view(request, entity_id):
    """
    Edit an existing entity.
    GET/POST /admin/entities/<id>/edit/
    """
    entity = get_object_or_404(Entity, pk=entity_id)

    if request.method == 'POST':
        form = EntityAdminForm(request.POST, entity_id=entity_id)
        if form.is_valid():
            data = form.cleaned_data
            old_subdomain = entity.subdomain
            entity.name        = data['name']
            entity.entity_type = data['entity_type']
            entity.subdomain   = data['subdomain']
            entity.admin_user  = data.get('admin_user')
            entity.status      = data['status']
            entity.city        = data.get('city', '')
            entity.country     = data.get('country', '')
            entity.website     = data.get('website', '')
            entity.save()  # save() syncs is_active

            # If subdomain changed and entity is active, register new DNS record
            if entity.subdomain != old_subdomain and entity.is_active:
                try:
                    create_subdomain_dns_record(entity.subdomain)
                except Exception as exc:
                    logger.error('DNS registration failed for entity %s: %s', entity.subdomain, exc)

            messages.success(request, f'Entity "{entity.name}" updated.')
            return redirect('admin_entities_list')
    else:
        form = EntityAdminForm(
            initial={
                'name':        entity.name,
                'entity_type': entity.entity_type,
                'subdomain':   entity.subdomain,
                'admin_user':  entity.admin_user_id,
                'status':      entity.status,
                'city':        entity.city,
                'country':     entity.country,
                'website':     entity.website,
            },
            entity_id=entity_id,
        )

    return render(request, 'admin/entity_form.html', {
        'form': form,
        'entity': entity,
        'action': 'Edit',
        'page_title': f'Edit Entity — {entity.name}',
    })


@_admin_login_required
@require_http_methods(['POST'])
def entity_approve_view(request, entity_id):
    """
    Approve a pending entity → status=active, DNS registered.
    POST /admin/entities/<id>/approve/
    """
    entity = get_object_or_404(Entity, pk=entity_id, status='pending')
    entity.status = Entity.STATUS_ACTIVE
    entity.save()

    try:
        create_subdomain_dns_record(entity.subdomain)
    except Exception as exc:
        logger.error('DNS registration failed for entity %s: %s', entity.subdomain, exc)

    messages.success(request, f'Entity "{entity.name}" approved and activated.')
    return redirect('admin_entities_list')


@_admin_login_required
@require_http_methods(['POST'])
def entity_reject_view(request, entity_id):
    """
    Reject a pending entity → status=suspended.
    POST /admin/entities/<id>/reject/
    """
    entity = get_object_or_404(Entity, pk=entity_id, status='pending')
    entity.status = Entity.STATUS_SUSPENDED
    entity.save()

    messages.warning(request, f'Entity "{entity.name}" rejected.')
    return redirect('admin_entities_list')


@_admin_login_required
@require_http_methods(['POST'])
def entity_suspend_view(request, entity_id):
    """
    Suspend an active entity → status=suspended, is_active=False.
    POST /admin/entities/<id>/suspend/
    """
    entity = get_object_or_404(Entity, pk=entity_id)
    entity.status = Entity.STATUS_SUSPENDED
    entity.save()

    messages.warning(request, f'Entity "{entity.name}" suspended.')
    return redirect('admin_entities_list')


@_admin_login_required
@require_http_methods(['POST'])
def entity_reactivate_view(request, entity_id):
    """
    Reactivate a suspended entity → status=active, DNS registered if needed.
    POST /admin/entities/<id>/reactivate/
    """
    entity = get_object_or_404(Entity, pk=entity_id)
    entity.status = Entity.STATUS_ACTIVE
    entity.save()

    try:
        create_subdomain_dns_record(entity.subdomain)
    except Exception as exc:
        logger.error('DNS registration failed for entity %s: %s', entity.subdomain, exc)

    messages.success(request, f'Entity "{entity.name}" reactivated.')
    return redirect('admin_entities_list')
