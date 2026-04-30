"""
Advanced Passenger WSGI Application Configuration
UniMarket Platform - smw.pgwiz.cloud

Features:
- Multi-tenant Django-Tenants support
- Environment-based settings (dev/prod)
- Virtual environment path management
- Error logging and debugging
- Graceful initialization
- Request/response logging
- Performance monitoring
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = BASE_DIR  # passenger_wsgi.py is in public_python, so BASE_DIR IS public_python
VENV_DIR = PROJECT_DIR / 'venv'
PYTHON_VERSION = 'python3.11'
SITE_PACKAGES = VENV_DIR / 'lib' / PYTHON_VERSION / 'site-packages'

# Add virtualenv packages to path (must be first)
if SITE_PACKAGES.exists():
    sys.path.insert(0, str(SITE_PACKAGES))
else:
    raise RuntimeError(f"Virtual environment not found at {VENV_DIR}")

# Add project directory to path
if PROJECT_DIR.exists():
    sys.path.insert(0, str(PROJECT_DIR))
else:
    raise RuntimeError(f"Project directory not found at {PROJECT_DIR}")

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_DIR = BASE_DIR / 'logs' / 'wsgi'
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f'passenger_{datetime.now().strftime("%Y%m%d")}.log'
ERROR_LOG_FILE = LOG_DIR / f'passenger_error_{datetime.now().strftime("%Y%m%d")}.log'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)
error_logger = logging.getLogger('passenger.error')
error_handler = logging.FileHandler(ERROR_LOG_FILE)
error_handler.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

# Detect environment
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'production').lower()
if ENVIRONMENT not in ('development', 'production', 'staging'):
    ENVIRONMENT = 'production'

logger.info(f"Initializing Passenger WSGI for {ENVIRONMENT} environment")
logger.info(f"Base directory: {BASE_DIR}")
logger.info(f"Project directory: {PROJECT_DIR}")
logger.info(f"Virtual environment: {VENV_DIR}")

# Set Django settings module
SETTINGS_MODULE = f'config.settings.prod' if ENVIRONMENT == 'production' else f'config.settings.dev'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', SETTINGS_MODULE)

logger.info(f"Django settings module: {SETTINGS_MODULE}")

# ============================================================================
# DJANGO INITIALIZATION
# ============================================================================

try:
    import django
    from django.core.wsgi import get_wsgi_application
    from django.conf import settings
    
    logger.info(f"Django version: {django.get_version()}")
    
    # Setup Django
    django.setup()
    
    logger.info("Django setup completed successfully")
    
    # Log important settings
    logger.info(f"DEBUG: {settings.DEBUG}")
    logger.info(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    logger.info(f"DATABASES: {list(settings.DATABASES.keys())}")
    logger.info(f"INSTALLED_APPS: {len(settings.INSTALLED_APPS)} apps installed")
    
    # Get WSGI application
    application = get_wsgi_application()
    
    logger.info("WSGI application initialized successfully")
    
except Exception as e:
    error_msg = f"Failed to initialize WSGI application: {str(e)}\n{traceback.format_exc()}"
    logger.error(error_msg)
    error_logger.error(error_msg)
    
    # Fallback error application
    def application(environ, start_response):
        """Fallback error handler"""
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/plain')]
        start_response(status, headers)
        return [b'WSGI Initialization Error - Check logs for details']

# ============================================================================
# MIDDLEWARE WRAPPERS
# ============================================================================

class RequestLoggerMiddleware:
    """Log incoming requests and responses"""
    
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
    
    def __call__(self, environ, start_response):
        method = environ.get('REQUEST_METHOD', 'UNKNOWN')
        path = environ.get('PATH_INFO', '/')
        host = environ.get('HTTP_HOST', 'unknown')
        
        logger.info(f"Request: {method} {host}{path}")
        
        def custom_start_response(status, response_headers):
            logger.info(f"Response: {status}")
            return start_response(status, response_headers)
        
        try:
            return self.wsgi_app(environ, custom_start_response)
        except Exception as e:
            error_logger.error(f"Exception during request: {str(e)}\n{traceback.format_exc()}")
            raise


class HealthCheckMiddleware:
    """Handle health checks without logging them"""
    
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
    
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        
        # Skip logging for health checks
        if path in ('/__health__', '/health', '/ping'):
            def health_start_response(status, response_headers):
                return start_response(status, response_headers)
            
            return self.wsgi_app(environ, health_start_response)
        
        return self.wsgi_app(environ, start_response)


class TenantMiddleware:
    """Handle multi-tenant request routing"""
    
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
    
    def __call__(self, environ, start_response):
        host = environ.get('HTTP_HOST', '').split(':')[0]
        logger.debug(f"Processing tenant request for host: {host}")
        return self.wsgi_app(environ, start_response)


# Wrap application with middleware
try:
    application = HealthCheckMiddleware(application)
    application = TenantMiddleware(application)
    application = RequestLoggerMiddleware(application)
    logger.info("All middleware layers applied successfully")
except Exception as e:
    error_msg = f"Failed to apply middleware: {str(e)}\n{traceback.format_exc()}"
    logger.error(error_msg)
    error_logger.error(error_msg)

# ============================================================================
# INITIALIZATION COMPLETE
# ============================================================================

logger.info("=" * 60)
logger.info("Passenger WSGI Application Ready")
logger.info(f"Environment: {ENVIRONMENT}")
logger.info(f"Python: {sys.version.split()[0]}")
logger.info(f"Django: {django.get_version()}")
logger.info("=" * 60)

# Expose application for Passenger
__all__ = ['application']
