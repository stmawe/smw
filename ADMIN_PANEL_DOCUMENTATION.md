# Admin Panel Documentation

## Overview

The SMW Admin Panel is a comprehensive, role-based administration system that provides complete control over the entire platform. It features:

- **16+ Admin Pages** with professional Bootstrap 5 UI
- **RBAC System** with 5 role hierarchy and 30+ granular permissions
- **Complete CRUD Operations** for all major resources
- **Comprehensive Audit Logging** tracking every admin action
- **Real-time Activity Feed** for visibility
- **REST API Endpoints** for programmatic access
- **Django Signals Integration** for automatic tracking
- **Bulk Operations** for batch management

---

## RBAC Role Hierarchy

```
Superuser (System Owner)
  └─ Full access to all features
  
Admin (Platform Manager)
  └─ Create/edit/delete users, shops, listings, transactions
  └─ Manage settings and configurations
  └─ Access audit logs and analytics
  
Moderator (Content Manager)
  └─ Flag and approve/reject user content
  └─ View analytics (read-only)
  └─ Moderate user reports
  
Support (User Support)
  └─ View users and limited editing
  └─ Process refunds
  └─ Read-only analytics
  
Viewer (Analytics)
  └─ View-only access to dashboards and reports
```

---

## Permission System

### Available Permissions (30+)

```
User Management:
  - admin:manage_users - Create, edit, delete, suspend users
  - admin:view_users - View user list and details
  - admin:manage_user_roles - Assign admin roles
  - admin:delete_users - Permanently delete users
  - admin:suspend_users - Suspend/activate users
  - admin:manage_passwords - Change user passwords

Shop Management:
  - admin:manage_shops - Create, edit, delete shops
  - admin:view_shops - View shop list and details
  - admin:activate_shops - Activate/deactivate shops
  - admin:delete_shops - Permanently delete shops
  - admin:manage_shop_domains - Edit domains and SSL
  - admin:manage_shop_themes - Change shop themes

Listing Management:
  - admin:manage_listings - Edit/delete any listing
  - admin:view_listings - View all listings
  - admin:feature_listings - Feature/unfeature listings
  - admin:delete_listings - Permanently delete listings

Content Moderation:
  - admin:moderate_content - Flag, approve, reject content
  - admin:view_flags - View flagged content and reports
  - admin:ban_users - Ban users from platform
  - admin:delete_comments - Remove messages/comments

Transactions & Payments:
  - admin:manage_transactions - View and refund transactions
  - admin:view_transactions - View transaction history
  - admin:refund_transactions - Issue refunds
  - admin:manual_payment - Record manual payments

Categories & Catalog:
  - admin:manage_categories - Create/edit/delete categories
  - admin:view_categories - View categories

Site Settings:
  - admin:manage_settings - Change site-wide settings
  - admin:manage_email_config - SMTP configuration
  - admin:manage_payment_config - Payment gateway config
  - admin:manage_ssl_config - SSL settings
  - admin:manage_themes - Create/edit/delete themes
  - admin:manage_design_tokens - Edit design tokens

Analytics & Reporting:
  - admin:view_analytics - View analytics dashboard
  - admin:view_reports - Access reports
  - admin:export_data - Export data to CSV/PDF

Audit & Security:
  - admin:view_audit_logs - View admin action logs
  - admin:manage_admins - Invite/manage admin team
  - admin:manage_security - Security settings (2FA, IP whitelist)

Tenant Management:
  - admin:manage_tenants - Create/edit tenants (multi-tenant only)
  - admin:manage_billing - Manage customer billing

System:
  - admin:access_admin_panel - Access admin panel at all
```

### Using Permissions in Views

```python
from app.admin_permissions import permission_required, AdminPermission

# Decorator usage
@login_required
@permission_required(AdminPermission.MANAGE_USERS)
def admin_users_list(request):
    # Only users with MANAGE_USERS permission can access
    pass

# Template usage
{% if perms.admin.manage_users %}
  <a href="...">Edit User</a>
{% endif %}

# Request object usage
if request.admin_perms.has(AdminPermission.MANAGE_USERS):
    # Show edit button
    pass
```

---

## Admin Pages & Endpoints

### Dashboard
- **URL**: `/admin/dashboard/`
- **Purpose**: Overview with key metrics and activity feed
- **Permissions**: `admin:access_admin_panel`
- **Features**: 
  - Key metrics cards (users, shops, listings)
  - Recent activity feed
  - Pending items count
  - Quick action buttons

### User Management
- **List**: `/admin/users/`
- **Detail**: `/admin/user/<id>/`
- **Suspend**: `/admin/user/<id>/suspend/`
- **Permissions**: `admin:manage_users`, `admin:suspend_users`
- **Features**:
  - Search by username/email
  - Filter by role and staff status
  - Bulk suspend/unsuspend
  - Edit user details and password
  - View user statistics

### Shop Management
- **List**: `/admin/shops/`
- **Detail**: `/admin/shop/<id>/`
- **Permissions**: `admin:manage_shops`
- **Features**:
  - Search shops
  - Filter by status (active/inactive)
  - View shop statistics
  - Edit shop details
  - Manage domain and SSL
  - View listings and transactions

### Listing Management
- **Moderation**: `/admin/listings/moderation/`
- **Detail**: `/admin/listing/<id>/`
- **Flag**: `/admin/listing/<id>/flag/`
- **Permissions**: `admin:manage_listings`, `admin:moderate_content`
- **Features**:
  - Moderation queue for pending listings
  - Approve/reject listings
  - Feature/unfeature listings
  - Flag for review
  - Bulk approve/reject
  - View listing details and flags

### Moderation Center
- **URL**: `/admin/moderation/`
- **Permissions**: `admin:moderate_content`
- **Features**:
  - Flagged content tab
  - User reports tab
  - Banned users tab
  - Flag management
  - User banning system

### Category Management
- **URL**: `/admin/categories/`
- **Create**: `/admin/category/create/` (POST)
- **Delete**: `/admin/category/<id>/delete/` (POST)
- **Permissions**: `admin:manage_categories`
- **Features**:
  - List all categories
  - Create new category
  - Delete categories (with validation)

### Transaction Management
- **List**: `/admin/transactions/`
- **Refund**: `/admin/transaction/<id>/refund/` (POST)
- **Permissions**: `admin:manage_transactions`, `admin:refund_transactions`
- **Features**:
  - Transaction history with search
  - Filter by status
  - Process refunds
  - View transaction details

### Analytics & Reports
- **URL**: `/admin/analytics/`
- **API**: `/admin/api/analytics/summary/`
- **Top Sellers API**: `/admin/api/analytics/top-sellers/`
- **Permissions**: `admin:view_analytics`
- **Features**:
  - Revenue metrics over time
  - User growth trends
  - Top sellers ranking
  - Category performance
  - Transaction breakdown

### Settings
- **URL**: `/admin/settings/`
- **Permissions**: `admin:manage_settings`
- **Features**:
  - General settings tab
  - Payment configuration
  - Email configuration
  - Security settings
  - Theme settings

### Theme Management
- **List**: `/admin/themes/`
- **Activate**: `/admin/theme/<id>/activate/` (POST)
- **Permissions**: `admin:manage_themes`
- **Features**:
  - Create/edit themes
  - Color customization
  - Font selection
  - Preview themes
  - Activate/deactivate

### Audit Logs
- **List**: `/admin/audit-logs/`
- **Detail**: `/admin/audit-log/<id>/`
- **Permissions**: `admin:view_audit_logs`
- **Features**:
  - Comprehensive action history
  - Filter by admin, action, content type
  - View before/after values
  - Reason and error tracking
  - CSV export

---

## REST API Endpoints

### Users API

```
GET /admin/api/users/
  - List all users with pagination and filtering
  - Query params: page, per_page, search, role, is_staff

GET /admin/api/users/<id>/permissions/
  - Get all permissions for a user

POST /admin/api/users/<id>/update/
  - Update user via API (JSON payload)
```

### Shops API

```
GET /admin/api/shops/
  - List all shops with pagination
  - Query params: page, per_page, search, status
```

### Listings API

```
GET /admin/api/listings/
  - List listings with filtering
  - Query params: page, per_page, search, status

POST /admin/api/listings/<id>/action/
  - Perform action (approve, reject, feature, unfeature)
  - Payload: {"action": "approve", "reason": "..."}
```

### Transactions API

```
GET /admin/api/transactions/
  - List transactions
  - Query params: page, per_page, status

POST /admin/api/transactions/<id>/refund/
  - Process refund
  - Payload: {"reason": "..."}
```

### Audit Logs API

```
GET /admin/api/audit-logs/
  - List audit logs with filtering
  - Query params: page, per_page, action, admin_id, content_type

GET /admin/api/audit-logs/<id>/
  - Get detailed audit log entry
```

### Analytics API

```
GET /admin/api/analytics/summary/
  - Get summary statistics
  - Query params: days (default: 30)

GET /admin/api/analytics/top-sellers/
  - Get top sellers ranking
  - Query params: days, sort_by (count|revenue), limit
```

### Activity Feed API

```
GET /admin/api/activity-feed/
  - Get recent activity
  - Query params: limit (default: 50)

GET /admin/api/activity-updates/
  - Get activity updates (for real-time feed)
  - Query params: since (ISO timestamp)
```

---

## Admin Models

### AdminAuditLog

Tracks every admin action with full context.

```python
Fields:
  - admin_user: ForeignKey(User) - Who performed the action
  - admin_username: str - Snapshot of username
  - action: str - Action type (create, update, delete, etc.)
  - action_label: str - Human-readable label
  - content_type: str - Model name (User, Shop, Listing, etc.)
  - object_id: str - ID of affected object
  - object_str: str - String representation of object
  - changes: JSONField - {field: {old: value, new: value}}
  - old_values: JSONField - Full before snapshot
  - new_values: JSONField - Full after snapshot
  - reason: str - Why the action was taken
  - ip_address: str - Admin's IP address
  - user_agent: str - Admin's browser/client info
  - status: str - success, error, partial_success, pending
  - error_message: str - Error details if status=error
  - created_at: datetime - When the action occurred

Indexing:
  - (admin_user, created_at)
  - (action, created_at)
  - (content_type, object_id)
  - (created_at)
```

### AdminActivityFeed

User-friendly activity stream for dashboard.

```python
Fields:
  - admin_user: ForeignKey(User) - Who performed action
  - activity_type: str - created, updated, deleted, approved, banned, etc.
  - content_type: str - Model name
  - object_id: str - ID of object
  - object_title: str - Human-readable title
  - description: str - Short description for dashboard
  - icon: str - Bootstrap icon name
  - severity: str - info, success, warning, danger
  - link_url: str - URL to affected object
  - batch_id: str - For grouping bulk operations
  - is_visible: bool - Show in activity feed?
  - created_at: datetime

Indexing:
  - (admin_user, created_at)
  - (activity_type, created_at)
  - (content_type, object_id)
  - (created_at)
```

---

## Audit Logging

### Manual Logging (in views)

```python
from app.admin_crud_views import log_admin_action, log_activity_feed

# Log audit action
log_admin_action(
    request,
    'update',           # action type
    'User',             # content_type
    user.id,            # object_id
    user.email,         # object_str
    changes={'email': {'old': 'old@email.com', 'new': 'new@email.com'}},
    reason='Email updated by admin',
    status='success'
)

# Log activity feed
log_activity_feed(
    request,
    'updated',          # activity_type
    'User',             # content_type
    user.id,            # object_id
    object_title=user.email,
    description=f'Updated user {user.email}',
    severity='info'
)
```

### Automatic Logging (via signals)

Signals are automatically registered for:
- User create/update/delete
- Shop create/update/delete
- Listing create/update/delete
- Transaction create/update
- Category create/update/delete

No need to call logging functions manually for these models.

---

## Utility Functions

### Statistics

```python
from app.admin_utils import (
    get_dashboard_stats,
    get_user_stats,
    get_shop_stats,
    get_admin_activity_summary
)

# Dashboard overview
stats = get_dashboard_stats()
# Returns: {total_users, total_shops, total_listings, revenue_week, ...}

# User-specific stats
user_stats = get_user_stats(user)
# Returns: {shops, listings, transactions, joined_days, ...}

# Shop-specific stats
shop_stats = get_shop_stats(shop)
# Returns: {total_listings, active_listings, total_revenue, ...}

# Activity summary
activity = get_admin_activity_summary(days=30)
# Returns: {total_actions, by_action, by_admin, errors, ...}
```

### Filtering

```python
from app.admin_utils import (
    filter_users,
    filter_shops,
    filter_listings,
    filter_transactions
)

# Filter users
users = filter_users(
    User.objects.all(),
    search='john',
    role='buyer',
    is_staff=False,
    is_active=True
)

# Filter shops
shops = filter_shops(Shop.objects.all(), search='store', is_active=True)

# Filter listings
listings = filter_listings(
    Listing.objects.all(),
    search='phone',
    status='pending',
    is_featured=False
)
```

### Exporting

```python
from app.admin_utils import (
    export_users_csv,
    export_shops_csv,
    export_transactions_csv
)

# Export users to CSV
response = export_users_csv(User.objects.all())

# Export shops to CSV
response = export_shops_csv(Shop.objects.all())

# Export transactions to CSV
response = export_transactions_csv(Transaction.objects.all())
```

---

## Bulk Operations

### Listing Bulk Actions

```
POST /admin/listings/bulk-action/

Params:
  - action: approve, reject, delete, feature
  - listing_ids: [1, 2, 3, ...]
  - reason: "Reason for bulk action"

Returns:
  - Success message with count of affected items
```

### User Bulk Actions

```
POST /admin/users/bulk-action/

Params:
  - action: suspend, unsuspend, delete
  - user_ids: [1, 2, 3, ...]
  - reason: "Reason for bulk action"

Returns:
  - Success message with count of affected items
```

---

## Component Library

### Available Components

All components are in `templates/admin/components/`:

1. **card.html** - Container with header/body/footer
2. **badge.html** - Status badges
3. **table.html** - Sortable, selectable data table
4. **pagination.html** - Page navigation
5. **filter_bar.html** - Search and filter controls
6. **modal.html** - Dialog component
7. **bulk_actions.html** - Bulk action toolbar
8. **stat_card.html** - Dashboard metric cards
9. **status_indicator.html** - Status display
10. **breadcrumbs.html** - Breadcrumb navigation

### Using Components

```django
{% load admin_filters %}

<!-- Card -->
{% include 'admin/components/card.html' with title='Users' body=content %}

<!-- Table -->
{% include 'admin/components/table.html' with items=users headers=table_headers %}

<!-- Badge -->
{% include 'admin/components/badge.html' with status='active' label='Active' %}

<!-- Pagination -->
{% include 'admin/components/pagination.html' with page=page_num total_pages=total %}

<!-- Stat Card -->
{% include 'admin/components/stat_card.html' with title='Total Users' value=total_users %}
```

---

## Creating New Admin Pages

### Template Structure

```django
{% extends 'admin/base.html' %}

{% block title %}Page Title{% endblock %}

{% block breadcrumbs %}
  {% include 'admin/components/breadcrumbs.html' with items=breadcrumb_items %}
{% endblock %}

{% block content %}
<div class="admin-page">
  <h1>Page Title</h1>
  
  <!-- Search/Filter Bar -->
  {% include 'admin/components/filter_bar.html' with search_url='...' %}
  
  <!-- Bulk Actions -->
  {% include 'admin/components/bulk_actions.html' %}
  
  <!-- Data Table -->
  {% include 'admin/components/table.html' with items=items %}
  
  <!-- Pagination -->
  {% include 'admin/components/pagination.html' %}
</div>
{% endblock %}
```

### View Handler

```python
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.admin_permissions import permission_required, AdminPermission

@login_required
@permission_required(AdminPermission.YOUR_PERMISSION)
def your_admin_page(request):
    """Admin page view."""
    items = YourModel.objects.all()
    
    # Filtering
    search = request.GET.get('search', '')
    if search:
        items = items.filter(name__icontains=search)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = 50
    total = items.count()
    
    items_page = items[(page-1)*per_page:page*per_page]
    total_pages = (total + per_page - 1) // per_page
    
    context = {
        'items': items_page,
        'page': page,
        'total_pages': total_pages,
        'search': search,
    }
    
    return render(request, 'admin/your_page.html', context)
```

---

## Testing the Admin System

### Quick Start

```bash
# Create admin user
python manage.py seed_admins --include-demo

# Login credentials
Username: admins
Password: haha6admin

# Visit admin dashboard
http://localhost:8000/admin/dashboard/
```

### Test Audit Logging

```python
# In Django shell
python manage.py shell

from app.models import AdminAuditLog, AdminActivityFeed
from app.admin_crud_views import log_admin_action

# Check recent logs
AdminAuditLog.objects.all().order_by('-created_at')[:5]

# Check activity feed
AdminActivityFeed.objects.all().order_by('-created_at')[:10]
```

### Test Bulk Operations

1. Navigate to `/admin/users/`
2. Select multiple users with checkboxes
3. Choose "Suspend" from bulk actions dropdown
4. Click "Apply"
5. Verify audit logs recorded each action

---

## Performance Considerations

### Database Indexes

All models have proper indexing:
- `AdminAuditLog`: (admin_user, created_at), (action, created_at), (content_type, object_id)
- `AdminActivityFeed`: Similar for fast queries

### Caching

```python
from app.admin_utils import get_cached_dashboard_stats

# Uses Django cache (5-minute default)
stats = get_cached_dashboard_stats()

# Clear cache when needed
from app.admin_utils import clear_admin_cache
clear_admin_cache()
```

### Pagination

Always paginate list views:
- Default: 50 items per page
- Max: 100 items per page (API)

---

## Security

### CSRF Protection

All POST endpoints include CSRF protection via Django middleware.

### Permission Checking

Every view has permission checks:
- View-level: `@permission_required()` decorator
- Template-level: `{% if perms.admin.permission %}`
- Request-level: `request.admin_perms.has()`

### Audit Trail

Every action is logged with:
- Admin user attribution
- IP address
- User agent
- Before/after values
- Error tracking

### Input Validation

All forms validated before database operations.

---

## Troubleshooting

### Admin can't access panel

1. Check user has `is_staff=True`
2. Verify `AdminRolesMiddleware` in MIDDLEWARE
3. Check permission decorators

### Signals not working

1. Verify `admin_signals` imported in `AppConfig.ready()`
2. Check migration applied: `python manage.py migrate`

### Audit logs missing

1. Check `AdminAuditLog` model in database
2. Verify `log_admin_action()` called in views
3. Check signals registered for models

### Performance issues

1. Check database indexes exist
2. Paginate large querysets
3. Use `select_related()` for foreign keys
4. Clear admin cache if stale

---

## Future Enhancements

- [ ] 2FA authentication for admin accounts
- [ ] Email notifications for important actions
- [ ] IP whitelisting for admin panel
- [ ] Advanced search with full-text indexing
- [ ] API rate limiting for programmatic access
- [ ] WebSocket updates for real-time activity
- [ ] Advanced chart visualizations
- [ ] Backup and restore functionality

---

## Support & Documentation

For more information:
- Admin Permissions: See `app/admin_permissions.py`
- CRUD Views: See `app/admin_crud_views.py`
- Advanced Views: See `app/admin_advanced_views.py`
- REST API: See `app/admin_api.py`
- Utility Functions: See `app/admin_utils.py`
