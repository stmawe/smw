"""
Admin data export functionality for CSV and PDF exports.
Supports exporting users, shops, listings, transactions, and analytics.
"""

import csv
import io
import json
from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Avg
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from app.models import AdminAuditLog
from mydak.models import Shop, Listing, Transaction, Category
from app.admin_utils import log_admin_action, permission_required
from app.admin_permissions import AdminPermission


class AdminDataExporter:
    """Handles exporting admin data in various formats."""
    
    @staticmethod
    def export_users_csv(queryset, fields=None):
        """Export users to CSV."""
        if fields is None:
            fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(fields)
        
        for user in queryset:
            row = []
            for field in fields:
                value = getattr(user, field, '')
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                row.append(value)
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_shops_csv(queryset, fields=None):
        """Export shops to CSV."""
        if fields is None:
            fields = ['id', 'name', 'owner__username', 'is_active', 'created_at', 'updated_at']
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(fields)
        
        for shop in queryset.select_related('owner'):
            row = []
            for field in fields:
                if '__' in field:
                    parts = field.split('__')
                    value = shop
                    for part in parts:
                        value = getattr(value, part, '')
                else:
                    value = getattr(shop, field, '')
                
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                row.append(value)
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_listings_csv(queryset, fields=None):
        """Export listings to CSV."""
        if fields is None:
            fields = ['id', 'title', 'shop__name', 'category__name', 'price', 'status', 'created_at']
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(fields)
        
        for listing in queryset.select_related('shop', 'category'):
            row = []
            for field in fields:
                if '__' in field:
                    parts = field.split('__')
                    value = listing
                    for part in parts:
                        value = getattr(value, part, '')
                else:
                    value = getattr(listing, field, '')
                
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                row.append(value)
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_transactions_csv(queryset, fields=None):
        """Export transactions to CSV."""
        if fields is None:
            fields = ['id', 'user__username', 'shop__name', 'amount', 'status', 'created_at']
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(fields)
        
        for transaction in queryset.select_related('user', 'shop'):
            row = []
            for field in fields:
                if '__' in field:
                    parts = field.split('__')
                    value = transaction
                    for part in parts:
                        value = getattr(value, part, '')
                else:
                    value = getattr(transaction, field, '')
                
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                row.append(value)
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_audit_logs_csv(queryset):
        """Export audit logs to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['id', 'admin', 'action', 'resource_type', 'resource_id', 'status', 'created_at'])
        
        for log in queryset:
            writer.writerow([
                log.id,
                str(log.admin) if log.admin else 'System',
                log.action,
                log.resource_type,
                log.resource_id,
                log.status,
                log.created_at.isoformat(),
            ])
        
        return output.getvalue()
    
    @staticmethod
    def get_analytics_report(days=30):
        """Generate analytics report for specified period."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Users stats
        users_count = User.objects.filter(date_joined__range=[start_date, end_date]).count()
        active_users = User.objects.filter(is_active=True).count()
        
        # Shops stats
        shops_count = Shop.objects.filter(created_at__range=[start_date, end_date]).count()
        active_shops = Shop.objects.filter(is_active=True).count()
        
        # Listings stats
        listings_count = Listing.objects.filter(created_at__range=[start_date, end_date]).count()
        featured_listings = Listing.objects.filter(is_featured=True).count()
        
        # Transactions stats
        transactions = Transaction.objects.filter(created_at__range=[start_date, end_date])
        transaction_count = transactions.count()
        transaction_amount = transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days,
            },
            'users': {
                'new_users': users_count,
                'total_active': active_users,
            },
            'shops': {
                'new_shops': shops_count,
                'total_active': active_shops,
            },
            'listings': {
                'new_listings': listings_count,
                'total_featured': featured_listings,
            },
            'transactions': {
                'count': transaction_count,
                'total_amount': float(transaction_amount),
            },
        }


@require_http_methods(["GET"])
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
def export_users(request):
    """Export users list to CSV."""
    queryset = User.objects.all()
    
    # Apply filters
    search = request.GET.get('search', '').strip()
    if search:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(username__icontains=search) | Q(email__icontains=search)
        )
    
    is_active = request.GET.get('is_active')
    if is_active in ['true', 'false']:
        queryset = queryset.filter(is_active=is_active == 'true')
    
    csv_data = AdminDataExporter.export_users_csv(queryset)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    log_admin_action(request, 'EXPORT_USERS', 'User', queryset.count(), 'success')
    return response


@require_http_methods(["GET"])
@permission_required(AdminPermission.VIEW_SHOPS)
def export_shops(request):
    """Export shops list to CSV."""
    queryset = Shop.objects.all()
    
    search = request.GET.get('search', '').strip()
    if search:
        from django.db.models import Q
        queryset = queryset.filter(Q(name__icontains=search))
    
    is_active = request.GET.get('is_active')
    if is_active in ['true', 'false']:
        queryset = queryset.filter(is_active=is_active == 'true')
    
    csv_data = AdminDataExporter.export_shops_csv(queryset)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="shops_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    log_admin_action(request, 'EXPORT_SHOPS', 'Shop', queryset.count(), 'success')
    return response


@require_http_methods(["GET"])
@permission_required(AdminPermission.VIEW_LISTINGS)
def export_listings(request):
    """Export listings to CSV."""
    queryset = Listing.objects.all()
    
    search = request.GET.get('search', '').strip()
    if search:
        from django.db.models import Q
        queryset = queryset.filter(Q(title__icontains=search))
    
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)
    
    csv_data = AdminDataExporter.export_listings_csv(queryset)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="listings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    log_admin_action(request, 'EXPORT_LISTINGS', 'Listing', queryset.count(), 'success')
    return response


@require_http_methods(["GET"])
@permission_required(AdminPermission.VIEW_TRANSACTIONS)
def export_transactions(request):
    """Export transactions to CSV."""
    queryset = Transaction.objects.all()
    
    # Date range filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date)
    
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)
    
    csv_data = AdminDataExporter.export_transactions_csv(queryset)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="transactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    log_admin_action(request, 'EXPORT_TRANSACTIONS', 'Transaction', queryset.count(), 'success')
    return response


@require_http_methods(["GET"])
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
def export_audit_logs(request):
    """Export audit logs to CSV."""
    queryset = AdminAuditLog.objects.all()
    
    # Date range filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date)
    
    action = request.GET.get('action')
    if action:
        queryset = queryset.filter(action=action)
    
    csv_data = AdminDataExporter.export_audit_logs_csv(queryset)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    return response


@require_http_methods(["GET"])
@permission_required(AdminPermission.VIEW_AUDIT_LOGS)
def export_analytics_report(request):
    """Export analytics report as JSON."""
    days = int(request.GET.get('days', 30))
    report = AdminDataExporter.get_analytics_report(days)
    
    response = HttpResponse(json.dumps(report, indent=2), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="analytics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    return response
