"""
Admin request logging middleware.
Logs all admin endpoint requests with method, status, response time, and IP address.
"""

import logging
import time
import json
from django.utils.deprecation import MiddlewareNotUsed
from django.urls import resolve, Resolver404
from app.models import AdminAuditLog


logger = logging.getLogger('admin_requests')


class AdminRequestLoggingMiddleware:
    """
    Middleware to log all admin endpoint requests.
    Tracks method, status, response time, IP, and user agent.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_paths = ['/admin/', '/api/admin/']
    
    def __call__(self, request):
        # Check if this is an admin request
        if not self.is_admin_request(request.path):
            return self.get_response(request)
        
        # Record start time
        request.start_time = time.time()
        
        # Process request
        try:
            response = self.get_response(request)
        except Exception as e:
            # Log error
            self.log_request(request, None, str(e), is_error=True)
            raise
        
        # Log request
        self.log_request(request, response, None, is_error=False)
        
        return response
    
    @staticmethod
    def is_admin_request(path):
        """Check if path is admin endpoint."""
        admin_paths = ['/admin/', '/api/admin/']
        return any(path.startswith(p) for p in admin_paths)
    
    @staticmethod
    def log_request(request, response, error=None, is_error=False):
        """Log admin request with full context."""
        # Calculate response time
        response_time = time.time() - request.start_time if hasattr(request, 'start_time') else 0
        
        # Get response status
        status_code = response.status_code if response else 500
        
        # Get user info
        user = request.user if request.user.is_authenticated else None
        
        # Get IP address
        ip_address = AdminRequestLoggingMiddleware.get_client_ip(request)
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        
        # Get view function/name
        try:
            match = resolve(request.path)
            view_name = f"{match.func.__module__}.{match.func.__name__}"
        except Resolver404:
            view_name = "unknown"
        
        # Create log entry
        log_data = {
            'method': request.method,
            'path': request.path[:500],
            'status_code': status_code,
            'response_time_ms': round(response_time * 1000, 2),
            'user': str(user) if user else 'Anonymous',
            'user_id': user.id if user else None,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'view': view_name,
            'is_error': is_error,
            'error_message': error,
            'timestamp': time.time(),
        }
        
        # Log to file/stdout
        log_level = logging.ERROR if is_error else logging.INFO
        logger.log(
            log_level,
            f"{request.method} {request.path} {status_code} - {response_time:.2f}s",
            extra=log_data
        )
        
        # Also log to AdminAuditLog if it's a write operation
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            try:
                AdminAuditLog.objects.create(
                    admin=user if user and user.is_staff else None,
                    action=f"{request.method}_{view_name}",
                    resource_type='AdminRequest',
                    resource_id=None,
                    status='error' if is_error else 'success',
                    response_code=status_code,
                    details=json.dumps({
                        'path': request.path,
                        'ip_address': ip_address,
                        'user_agent': user_agent[:200],
                        'response_time_ms': round(response_time * 1000, 2),
                        'error': error,
                    }, default=str),
                )
            except Exception:
                pass  # Don't fail if audit logging fails
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


class AdminRequestMetricsMiddleware:
    """
    Middleware to track admin request metrics for monitoring.
    Provides request count, error rate, and performance stats.
    """
    
    # In-memory metrics (in production, use Redis or metrics service)
    REQUEST_COUNTS = {}
    ERROR_COUNTS = {}
    RESPONSE_TIMES = {}
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if not AdminRequestLoggingMiddleware.is_admin_request(request.path):
            return self.get_response(request)
        
        request.start_time = time.time()
        
        try:
            response = self.get_response(request)
        except Exception:
            self.record_metrics(request, 500)
            raise
        
        self.record_metrics(request, response.status_code)
        return response
    
    @classmethod
    def record_metrics(cls, request, status_code):
        """Record request metrics."""
        response_time = time.time() - request.start_time
        path = request.path
        
        # Count requests by path
        if path not in cls.REQUEST_COUNTS:
            cls.REQUEST_COUNTS[path] = 0
        cls.REQUEST_COUNTS[path] += 1
        
        # Count errors
        if status_code >= 400:
            if path not in cls.ERROR_COUNTS:
                cls.ERROR_COUNTS[path] = 0
            cls.ERROR_COUNTS[path] += 1
        
        # Track response times
        if path not in cls.RESPONSE_TIMES:
            cls.RESPONSE_TIMES[path] = []
        cls.RESPONSE_TIMES[path].append(response_time)
        
        # Keep last 1000 samples
        if len(cls.RESPONSE_TIMES[path]) > 1000:
            cls.RESPONSE_TIMES[path] = cls.RESPONSE_TIMES[path][-1000:]
    
    @classmethod
    def get_metrics(cls):
        """Get current metrics."""
        metrics = {}
        
        for path in cls.REQUEST_COUNTS:
            count = cls.REQUEST_COUNTS[path]
            errors = cls.ERROR_COUNTS.get(path, 0)
            times = cls.RESPONSE_TIMES.get(path, [])
            
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
            else:
                avg_time = max_time = min_time = 0
            
            metrics[path] = {
                'request_count': count,
                'error_count': errors,
                'error_rate': round((errors / count * 100) if count > 0 else 0, 2),
                'avg_response_time_ms': round(avg_time * 1000, 2),
                'max_response_time_ms': round(max_time * 1000, 2),
                'min_response_time_ms': round(min_time * 1000, 2),
            }
        
        return metrics
    
    @classmethod
    def reset_metrics(cls):
        """Reset all metrics."""
        cls.REQUEST_COUNTS.clear()
        cls.ERROR_COUNTS.clear()
        cls.RESPONSE_TIMES.clear()


def get_request_logging_config():
    """
    Django LOGGING configuration for request logging.
    Add this to your settings.py:
    
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'json': {
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
            }
        },
        'handlers': {
            'admin_requests_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(BASE_DIR, 'logs', 'admin_requests.log'),
                'maxBytes': 1024 * 1024 * 100,  # 100MB
                'backupCount': 10,
                'formatter': 'json',
            },
            'admin_requests_console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'admin_requests': {
                'handlers': ['admin_requests_file', 'admin_requests_console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
    """
    return """
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {message}',
                'style': '{',
            },
            'json': {
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            }
        },
        'handlers': {
            'admin_requests_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(BASE_DIR, 'logs', 'admin_requests.log'),
                'maxBytes': 1024 * 1024 * 100,
                'backupCount': 10,
                'formatter': 'json',
            },
        },
        'loggers': {
            'admin_requests': {
                'handlers': ['admin_requests_file'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
    """
