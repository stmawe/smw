{% comment %}
ADMIN COMPONENTS LIBRARY
=========================

This directory contains reusable template components for the admin panel.
Each component is designed to be included in admin pages and supports customization.

COMPONENTS:
-----------

1. card.html
   Purpose: Generic container for content
   Usage: {% include "admin/components/card.html" with title="Title" icon="bi-chart" %}
   
2. badge.html
   Purpose: Status/label badges
   Usage: {% include "admin/components/badge.html" with status="active" text="Active" %}
   
3. table.html
   Purpose: Data table with optional sorting, row selection, actions
   Usage: {% include "admin/components/table.html" with headers=headers rows=rows selectable=True %}
   
4. pagination.html
   Purpose: Page navigation for list views
   Usage: {% include "admin/components/pagination.html" with page_obj=page_obj %}
   
5. filter_bar.html
   Purpose: Search and filter controls
   Usage: {% include "admin/components/filter_bar.html" with search_placeholder="Search..." filters=filters %}
   
6. modal.html
   Purpose: Dialog boxes for confirmations, forms, etc.
   Usage: {% include "admin/components/modal.html" with modal_id="deleteModal" title="Confirm Delete" %}
   
7. bulk_actions.html
   Purpose: Toolbar for bulk operations on multiple items
   Usage: {% include "admin/components/bulk_actions.html" with actions=bulk_actions %}
   
8. stat_card.html
   Purpose: Dashboard metric display card
   Usage: {% include "admin/components/stat_card.html" with title="Users" value="1,234" icon="bi-people" color="primary" %}
   
9. status_indicator.html
   Purpose: Visual status indicator (active/inactive/pending/etc)
   Usage: {% include "admin/components/status_indicator.html" with status="active" %}
   
10. breadcrumbs.html
    Purpose: Navigation breadcrumbs
    Usage: {% include "admin/components/breadcrumbs.html" with items=breadcrumbs %}

COMMON PATTERNS:
----------------

Bootstrap 5 Grid System:
  - Use col-md-6, col-lg-4 for responsive layouts
  - Use row class with g-2/g-3/g-4 for gutters

Icons:
  - Use Bootstrap Icons (bi-*) for consistency
  - Examples: bi-pencil, bi-trash, bi-check, bi-x, bi-search, bi-plus

Colors:
  - primary, success, warning, danger, info, secondary
  - Use for badges, buttons, backgrounds

Responsive:
  - Mobile-first approach
  - Classes like d-none, d-md-block for conditional display
  - Breakpoints: xs (mobile), sm, md, lg, xl, xxl

EXAMPLE PAGE STRUCTURE:
-----------------------

{% extends "admin/base.html" %}
{% load static %}

{% block title %}Users - Admin{% endblock %}

{% block content %}
  <div class="container-fluid">
    <!-- Breadcrumbs -->
    {% include "admin/components/breadcrumbs.html" with items=breadcrumbs %}
    
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1>Users</h1>
      <button class="btn btn-primary">
        <i class="bi bi-plus"></i> Add User
      </button>
    </div>
    
    <!-- Filter Bar -->
    {% include "admin/components/filter_bar.html" with search_placeholder="Search users..." filters=filters %}
    
    <!-- Bulk Actions -->
    {% include "admin/components/bulk_actions.html" with actions=bulk_actions %}
    
    <!-- Table Card -->
    {% include "admin/components/card.html" with title="Users List" icon="bi-people" %}
      {% include "admin/components/table.html" with headers=table_headers rows=users selectable=True actions=row_actions %}
    {% endinclude %}
    
    <!-- Pagination -->
    {% include "admin/components/pagination.html" with page_obj=page_obj %}
  </div>
{% endblock %}

CUSTOM FILTERS NEEDED:
----------------------

Add these to a template filter file (e.g., app/templatetags/admin_filters.py):
  - dict_lookup: Access dict by key (for flexible table data)
  - add: Already built-in to Django

Example usage in template tags:
  {{ row|dict_lookup:"username" }}
{% endcomment %}
