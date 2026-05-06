"""
Public entity self-registration view.
Accessible at /register-entity/ without authentication.
Creates an Entity with status=pending awaiting admin approval.
"""

import logging

from django.contrib import messages
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from app.forms import EntityRegistrationForm
from app.models import Entity

logger = logging.getLogger(__name__)


@require_http_methods(['GET', 'POST'])
def entity_registration_view(request):
    """
    Public self-registration form for institutions.

    GET  → render blank form
    POST → validate; on success create Entity(status=pending), show confirmation
           on failure re-render with errors

    contact_email is logged (not stored on the Entity model).
    """
    if request.method == 'POST':
        form = EntityRegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Log contact email for admin follow-up (not stored on model)
            logger.info(
                'Entity self-registration: name="%s", subdomain="%s", contact="%s"',
                data['name'],
                data['subdomain'],
                data['contact_email'],
            )

            entity = Entity(
                name=data['name'],
                entity_type=data['entity_type'],
                subdomain=data['subdomain'],
                city=data.get('city', ''),
                country=data.get('country', ''),
                website=data.get('website', ''),
                status=Entity.STATUS_PENDING,  # pending until admin approves
                created_by=None,               # self-registered
            )
            entity.save()  # save() sets is_active=False (status=pending)

            messages.success(
                request,
                'Your registration has been submitted and is under review. '
                'We will contact you at the email you provided once it is approved.'
            )
            # Re-render with blank form and success message
            return render(request, 'entity_registration.html', {
                'form': EntityRegistrationForm(),
                'submitted': True,
            })
    else:
        form = EntityRegistrationForm()

    return render(request, 'entity_registration.html', {
        'form': form,
        'submitted': False,
    })
