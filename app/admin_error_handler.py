"""
Admin error handling middleware and utilities.
Logs errors with context and provides user-friendly error messages.
"""

import logging
import traceback
from django.http import JsonResponse
from django.shortcuts import render
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.http import require_http_methods
from app.admin_utils import log_admin_action

logger = logging.getLogger('admin_errors')


class AdminErrorHandlingMiddleware:
    """Middleware to log admin errors with context."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_exception(request, e)
    
    def handle_exception(self, request, exception):
        """Log exception with context and return appropriate response."""
        # Only log admin errors
        if not request.path.startswith('/admin/'):
            raise exception
        
        # Extract context
        context = {
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'path': request.path,
            'method': request.method,
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
        }
        
        # Log error
        logger.error(
            f"Admin Error: {exception.__class__.__name__}",
            exc_info=True,
            extra=context
        )
        
        # Return appropriate response
        if isinstance(exception, PermissionDenied):
            return self.error_403(request, exception)
        elif isinstance(exception, ObjectDoesNotExist):
            return self.error_404(request, exception)
        else:
            return self.error_500(request, exception)
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def error_403(request, exception=None):
    """403 Forbidden error handler."""
    context = {
        'title': 'Access Denied',
        'message': 'You do not have permission to access this resource.',
        'error_code': 403,
        'exception': str(exception) if exception else None,
    }
    
    if request.user.is_authenticated:
        context['user_info'] = f"User: {request.user.get_full_name() or request.user.username}"
    
    return render(request, 'admin/errors/403.html', context, status=403)


def error_404(request, exception=None):
    """404 Not Found error handler."""
    context = {
        'title': 'Page Not Found',
        'message': 'The page you are looking for does not exist.',
        'error_code': 404,
        'path': request.path,
        'exception': str(exception) if exception else None,
    }
    return render(request, 'admin/errors/404.html', context, status=404)


def error_500(request, exception=None):
    """500 Server Error handler."""
    context = {
        'title': 'Server Error',
        'message': 'An unexpected error occurred. Our team has been notified.',
        'error_code': 500,
        'exception': str(exception) if exception else None,
    }
    
    # Log with full traceback
    logger.error(
        "500 Server Error",
        exc_info=True,
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'path': request.path,
            'method': request.method,
        }
    )
    
    return render(request, 'admin/errors/500.html', context, status=500)


class AdminErrorLogger:
    """Utility for logging admin errors with context."""
    
    @staticmethod
    def log_error(request, error_type, message, **context):
        """Log an admin error with full context."""
        log_data = {
            'error_type': error_type,
            'message': message,
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'path': request.path,
            'method': request.method,
            'ip_address': AdminErrorHandlingMiddleware.get_client_ip(request),
            **context
        }
        
        logger.error(f"Admin Error: {error_type} - {message}", extra=log_data)
    
    @staticmethod
    def log_validation_error(request, form_data, errors):
        """Log form validation errors."""
        AdminErrorLogger.log_error(
            request,
            'VALIDATION_ERROR',
            f"Form validation failed with {len(errors)} errors",
            form_data=form_data,
            errors=errors
        )
    
    @staticmethod
    def log_permission_denied(request, resource, action):
        """Log permission denied errors."""
        AdminErrorLogger.log_error(
            request,
            'PERMISSION_DENIED',
            f"User attempted unauthorized {action} on {resource}",
            resource=resource,
            action=action
        )
    
    @staticmethod
    def log_database_error(request, operation, error):
        """Log database errors."""
        AdminErrorLogger.log_error(
            request,
            'DATABASE_ERROR',
            f"Database error during {operation}: {str(error)}",
            operation=operation,
            db_error=str(error)
        )


def handle_validation_error(request, errors):
    """Handle form validation errors and return JSON response."""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'message': 'Validation failed',
            'errors': errors
        }, status=400)
    
    # Log the error
    AdminErrorLogger.log_validation_error(request, {}, errors)
    
    # For non-AJAX requests, redirect back with messages
    from django.contrib import messages
    for field, field_errors in errors.items():
        for error in field_errors:
            messages.error(request, f"{field}: {error}")
    
    return None


def handle_permission_denied(request, resource, action='access'):
    """Handle permission denied and return appropriate response."""
    AdminErrorLogger.log_permission_denied(request, resource, action)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to perform this action.'
        }, status=403)
    
    raise PermissionDenied(f"You do not have permission to {action} this {resource}.")


def handle_not_found(request, resource_type, resource_id):
    """Handle resource not found and return appropriate response."""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'message': f'{resource_type} not found.'
        }, status=404)
    
    raise ObjectDoesNotExist(f"{resource_type} with ID {resource_id} not found.")
