from pathlib import Path
import os
import environ

# Initialize environment variables
env = environ.Env()
# Read .env file from the root (crm/) or one level up?
# If manage.py is in crm/, .env might be in crm/ or CRM/.
# Let's try to read from crm/ (BASE_DIR) and CRM/ (BASE_DIR.parent)
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-prod')
JWT_SECRET_KEY = env('JWT_SECRET_KEY', default=SECRET_KEY)
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'corsheaders',
    'django_filters',
    
    # Wagtail and its dependencies
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',
    'modelcluster',
    'taggit',

    # Local Apps
    'apps.core',
    'apps.users',
    'apps.crm',
    'apps.workflows',
    'apps.api',
    'apps.billing',
    'apps.audit',
    'apps.sales',
    'apps.marketing',
    'apps.analytics',
    'apps.omnichannel',
    'apps.portals',
    'apps.integrations',
    'encrypted_model_fields',
    'docs',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Custom Middleware
    'apps.core.middleware.TenantContextMiddleware',
    'apps.audit.middleware.AuditMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
                'apps.core.context_processors.frontend_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://dinesh@localhost:5432/crm_db'),
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DRF Config
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'apps.users.authentication.APIKeyAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'SIGNING_KEY': JWT_SECRET_KEY,
    'ALGORITHM': 'HS256',
}

GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID', default='')

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# CORS Settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

from celery.schedules import crontab

# Encryption
FIELD_ENCRYPTION_KEY = env('FIELD_ENCRYPTION_KEY', default='')

# AI Services  
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
OPENROUTER_API_KEY = env('OPENROUTER_API_KEY', default='')
AI_MODEL = env('AI_MODEL', default='openai/gpt-4o') # Default to OpenRouter model ID format

# Cache (for FLS and RBAC caching)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
    }
}

# Email (for workflow email.send action)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@novacrm.io')

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'sync-emails': {
        'task': 'apps.omnichannel.tasks.sync_all_email_integrations',
        'schedule': crontab(minute='*/15'),
    },
    'evaluate-scheduled-workflows': {
        'task': 'apps.workflows.tasks.evaluate_scheduled_workflows',
        'schedule': crontab(minute=0),
    },
    'generate-ai-deal-suggestions': {
        'task': 'apps.crm.tasks.generate_ai_suggestions_for_all_deals',
        'schedule': crontab(hour=2, minute=0),
    },
}

WAGTAIL_SITE_NAME = 'Nova CRM Documentation'
WAGTAILADMIN_BASE_URL = 'http://localhost:8000'
