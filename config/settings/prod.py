"""Production settings for UniMarket."""

from .base import *
from decouple import config, Csv

# Production-specific settings
DEBUG = True
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Production database from env
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django_tenants.postgresql_backend'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Add SSL options
DATABASES['default']['OPTIONS'] = {
    'sslmode': config('DB_SSLMODE', default='require'),
}
if config('DB_SSLROOTCERT', default=''):
    DATABASES['default']['OPTIONS']['sslrootcert'] = config('DB_SSLROOTCERT')

# Enable HTTPS/security features in production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Email in production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)

# Logging - less verbose in production
LOGGING['root']['level'] = 'INFO'

# Static files - use whitenoise or CDN in production
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
