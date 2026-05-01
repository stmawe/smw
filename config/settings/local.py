"""Local development settings with SQLite database"""

from .base import *
import os

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*.localhost', 'admin.localhost']

# Use SQLite for local development (no database setup needed)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db_local.sqlite3'),
    }
}

# Remove django_tenants from INSTALLED_APPS for local development
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django_tenants']

# Disable HTTPS/security features in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging configuration for local development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
