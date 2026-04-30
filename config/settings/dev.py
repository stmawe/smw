"""Development settings for UniMarket."""

from .base import *
from decouple import config, Csv

# Development-specific settings
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*.localhost']

# Development database (can override with env vars)
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': config('DB_NAME', default='smw'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Disable HTTPS/security features in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Enable Django Debug Toolbar in development (optional)
try:
    import debug_toolbar
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
except ImportError:
    pass

# Email in development - use console backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging - verbose in development
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers'] = {
    'django': {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False,
    },
}
