"""
Base settings for UniMarket project.
All environment-based configuration happens here.
"""

from pathlib import Path
from dotenv import load_dotenv
import os
from decouple import config, Csv

# Load environment variables
load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment
ENVIRONMENT = config('ENVIRONMENT', default='development')
DEBUG = config('DEBUG', default=True, cast=bool)

# Secret key
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# Allowed hosts
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Application definition
SHARED_APPS = [
    'daphne',
    'django_tenants',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'channels',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'app',
    'accounts',
    'apps.core',
    'apps.themes',
]

TENANT_APPS = [
    'django.contrib.contenttypes',
    'mydak',
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

# Tenant configuration
TENANT_MODEL = "app.Client"
TENANT_DOMAIN_MODEL = "app.ClientDomain"
PUBLIC_SCHEMA_NAME = config('PUBLIC_SCHEMA_NAME', default='public')
PUBLIC_SCHEMA_DOMAIN = config('PUBLIC_SCHEMA_DOMAIN', default='localhost')
BASE_DOMAIN = config('BASE_DOMAIN', default='localhost')
TENANT_SUBFOLDER_PREFIX = config('TENANT_SUBFOLDER_PREFIX', default='')

# Middleware
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smw.urls'

# Tenant URL configuration
TENANT_URLCONF = 'config.tenant_urls'  # URLs for tenant (sub-domain) requests
PUBLIC_SCHEMA_URLCONF = 'smw.urls'     # URLs for public schema requests

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.themes.context_processors.theme_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'smw.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(config('REDIS_HOST', default='127.0.0.1'), int(config('REDIS_PORT', default=6379)))],
            'db': int(config('REDIS_DB', default=0)),
        },
    },
}

# Database
DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django_tenants.postgresql_backend'),
        'NAME': config('DB_NAME', default='smw'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Add SSL options if provided
if config('DB_SSLMODE', default='disable') != 'disable':
    DATABASES['default']['OPTIONS'] = {
        'sslmode': config('DB_SSLMODE', default='require'),
    }
    if config('DB_SSLROOTCERT', default=''):
        DATABASES['default']['OPTIONS']['sslrootcert'] = config('DB_SSLROOTCERT')

# Auth
AUTH_USER_MODEL = 'app.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@unimarket.local')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)

# Security settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)

# Logging
LOG_LEVEL = config('LOG_LEVEL', default='INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
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
        'level': LOG_LEVEL,
    },
}

# Redis configuration (for caching and WebSockets)
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CACHE_BACKEND = config('CACHE_BACKEND', default='django.core.cache.backends.locmem.LocMemCache')

# M-Pesa configuration
MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='')
MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='')
MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='')
MPESA_PASSKEY = config('MPESA_PASSKEY', default='')
MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL', default='')
MPESA_SANDBOX = config('MPESA_SANDBOX', default=True, cast=bool)

# Storage configuration
USE_S3 = config('USE_S3', default=False, cast=bool)
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')

# AI features
CLAUDE_API_KEY = config('CLAUDE_API_KEY', default='')
CLAUDE_MODEL = config('CLAUDE_MODEL', default='claude-sonnet-4-20250514')

# Cloudflare API
CLOUDFLARE_API_TOKEN = config('CLOUDFLARE_API_TOKEN', default='')
CLOUDFLARE_ZONE_ID = config('CLOUDFLARE_ZONE_ID', default='')

# Django-Allauth Configuration
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth settings
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_EMAIL_VERIFICATION = config('ACCOUNT_EMAIL_VERIFICATION', default='optional')  # 'mandatory', 'optional', or 'none'
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'

# OAuth
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
    }
}

# Allauth redirects
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
