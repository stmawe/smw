"""
Admin data import functionality for bulk importing users, categories, and other resources.
Includes validation, error reporting, preview, and rollback support.
"""

import csv
import io
import json
from datetime import datetime
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User
from mydak.models import Category, Shop
from app.admin_utils import log_admin_action, permission_required
from app.admin_permissions import AdminPermission
from app.admin_validators import AdminFormValidators


class AdminDataImporter:
    """Handles bulk data imports with validation and rollback support."""
    
    @staticmethod
    def validate_csv_format(file_obj, expected_headers):
        """Validate CSV file format and headers."""
        try:
            # Read first line to check headers
            file_obj.seek(0)
            reader = csv.DictReader(file_obj)
            
            if not reader.fieldnames:
                return False, "CSV file is empty"
            
            # Check if all expected headers are present
            missing_headers = set(expected_headers) - set(reader.fieldnames)
            if missing_headers:
                return False, f"Missing required columns: {', '.join(missing_headers)}"
            
            return True, reader
        except Exception as e:
            return False, f"Error reading CSV: {str(e)}"
    
    @staticmethod
    def parse_csv_rows(file_obj):
        """Parse CSV rows into list of dictionaries."""
        file_obj.seek(0)
        reader = csv.DictReader(file_obj)
        return list(reader)
    
    @staticmethod
    def validate_user_row(row, existing_usernames=None):
        """Validate a single user row."""
        errors = []
        
        if existing_usernames is None:
            existing_usernames = set(User.objects.values_list('username', flat=True))
        
        # Check required fields
        if not row.get('username'):
            errors.append("Username is required")
        elif row['username'] in existing_usernames:
            errors.append(f"Username '{row['username']}' already exists")
        
        if not row.get('email'):
            errors.append("Email is required")
        else:
            try:
                AdminFormValidators.validate_email_unique(row['email'])
            except Exception as e:
                errors.append(str(e))
        
        if row.get('password'):
            try:
                AdminFormValidators.validate_strong_password(row['password'])
            except Exception as e:
                errors.append(str(e))
        
        return errors
    
    @staticmethod
    def validate_category_row(row, existing_names=None):
        """Validate a single category row."""
        errors = []
        
        if existing_names is None:
            existing_names = set(Category.objects.values_list('name', flat=True))
        
        if not row.get('name'):
            errors.append("Category name is required")
        elif row['name'] in existing_names:
            errors.append(f"Category '{row['name']}' already exists")
        
        return errors
    
    @staticmethod
    def preview_user_import(rows):
        """Generate preview for user import."""
        preview = {
            'total_rows': len(rows),
            'valid_rows': 0,
            'invalid_rows': 0,
            'rows': []
        }
        
        existing_usernames = set(User.objects.values_list('username', flat=True))
        
        for idx, row in enumerate(rows, 1):
            errors = AdminDataImporter.validate_user_row(row, existing_usernames)
            
            if errors:
                preview['invalid_rows'] += 1
                preview['rows'].append({
                    'row_number': idx,
                    'username': row.get('username', 'N/A'),
                    'valid': False,
                    'errors': errors
                })
            else:
                preview['valid_rows'] += 1
                preview['rows'].append({
                    'row_number': idx,
                    'username': row.get('username'),
                    'email': row.get('email'),
                    'valid': True,
                    'errors': []
                })
        
        return preview
    
    @staticmethod
    def preview_category_import(rows):
        """Generate preview for category import."""
        preview = {
            'total_rows': len(rows),
            'valid_rows': 0,
            'invalid_rows': 0,
            'rows': []
        }
        
        existing_names = set(Category.objects.values_list('name', flat=True))
        
        for idx, row in enumerate(rows, 1):
            errors = AdminDataImporter.validate_category_row(row, existing_names)
            
            if errors:
                preview['invalid_rows'] += 1
                preview['rows'].append({
                    'row_number': idx,
                    'name': row.get('name', 'N/A'),
                    'valid': False,
                    'errors': errors
                })
            else:
                preview['valid_rows'] += 1
                preview['rows'].append({
                    'row_number': idx,
                    'name': row.get('name'),
                    'description': row.get('description', ''),
                    'valid': True,
                    'errors': []
                })
        
        return preview
    
    @staticmethod
    def import_users(rows, created_by=None):
        """Import users from validated rows."""
        results = {
            'imported': 0,
            'failed': 0,
            'errors': [],
            'created_users': []
        }
        
        existing_usernames = set(User.objects.values_list('username', flat=True))
        
        with transaction.atomic():
            for idx, row in enumerate(rows, 1):
                try:
                    errors = AdminDataImporter.validate_user_row(row, existing_usernames)
                    if errors:
                        results['failed'] += 1
                        results['errors'].append({
                            'row': idx,
                            'errors': errors
                        })
                        continue
                    
                    # Create user
                    user = User.objects.create_user(
                        username=row['username'],
                        email=row['email'],
                        first_name=row.get('first_name', ''),
                        last_name=row.get('last_name', ''),
                    )
                    
                    if row.get('password'):
                        user.set_password(row['password'])
                        user.save()
                    
                    results['imported'] += 1
                    results['created_users'].append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    })
                    
                    existing_usernames.add(row['username'])
                
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'row': idx,
                        'error': str(e)
                    })
        
        return results
    
    @staticmethod
    def import_categories(rows):
        """Import categories from validated rows."""
        results = {
            'imported': 0,
            'failed': 0,
            'errors': [],
            'created_categories': []
        }
        
        existing_names = set(Category.objects.values_list('name', flat=True))
        
        with transaction.atomic():
            for idx, row in enumerate(rows, 1):
                try:
                    errors = AdminDataImporter.validate_category_row(row, existing_names)
                    if errors:
                        results['failed'] += 1
                        results['errors'].append({
                            'row': idx,
                            'errors': errors
                        })
                        continue
                    
                    # Create category
                    category = Category.objects.create(
                        name=row['name'],
                        description=row.get('description', '')
                    )
                    
                    results['imported'] += 1
                    results['created_categories'].append({
                        'id': category.id,
                        'name': category.name
                    })
                    
                    existing_names.add(row['name'])
                
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'row': idx,
                        'error': str(e)
                    })
        
        return results


@require_http_methods(["POST"])
@csrf_protect
@permission_required(AdminPermission.CREATE_USER)
def import_users_preview(request):
    """Preview user import from uploaded CSV."""
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    file_obj = request.FILES['file']
    
    # Validate CSV format
    is_valid, result = AdminDataImporter.validate_csv_format(
        file_obj,
        ['username', 'email']
    )
    
    if not is_valid:
        return JsonResponse({'error': result}, status=400)
    
    # Parse rows
    rows = AdminDataImporter.parse_csv_rows(file_obj)
    
    # Generate preview
    preview = AdminDataImporter.preview_user_import(rows)
    
    return JsonResponse(preview)


@require_http_methods(["POST"])
@csrf_protect
@permission_required(AdminPermission.CREATE_USER)
def import_users_execute(request):
    """Execute user import."""
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    file_obj = request.FILES['file']
    
    # Validate CSV format
    is_valid, result = AdminDataImporter.validate_csv_format(
        file_obj,
        ['username', 'email']
    )
    
    if not is_valid:
        return JsonResponse({'error': result}, status=400)
    
    # Parse rows
    rows = AdminDataImporter.parse_csv_rows(file_obj)
    
    # Import users
    results = AdminDataImporter.import_users(rows, request.user)
    
    # Log action
    log_admin_action(
        request,
        'IMPORT_USERS',
        'User',
        results['imported'],
        'success' if results['failed'] == 0 else 'partial'
    )
    
    return JsonResponse(results)


@require_http_methods(["POST"])
@csrf_protect
@permission_required(AdminPermission.CREATE_CATEGORY)
def import_categories_preview(request):
    """Preview category import from uploaded CSV."""
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    file_obj = request.FILES['file']
    
    # Validate CSV format
    is_valid, result = AdminDataImporter.validate_csv_format(
        file_obj,
        ['name']
    )
    
    if not is_valid:
        return JsonResponse({'error': result}, status=400)
    
    # Parse rows
    rows = AdminDataImporter.parse_csv_rows(file_obj)
    
    # Generate preview
    preview = AdminDataImporter.preview_category_import(rows)
    
    return JsonResponse(preview)


@require_http_methods(["POST"])
@csrf_protect
@permission_required(AdminPermission.CREATE_CATEGORY)
def import_categories_execute(request):
    """Execute category import."""
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    file_obj = request.FILES['file']
    
    # Validate CSV format
    is_valid, result = AdminDataImporter.validate_csv_format(
        file_obj,
        ['name']
    )
    
    if not is_valid:
        return JsonResponse({'error': result}, status=400)
    
    # Parse rows
    rows = AdminDataImporter.parse_csv_rows(file_obj)
    
    # Import categories
    results = AdminDataImporter.import_categories(rows)
    
    # Log action
    log_admin_action(
        request,
        'IMPORT_CATEGORIES',
        'Category',
        results['imported'],
        'success' if results['failed'] == 0 else 'partial'
    )
    
    return JsonResponse(results)
