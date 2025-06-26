"""
Django settings for mobilize project.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Force load Google OAuth credentials from .env file (override any system env vars)
env_file = Path(__file__).resolve().parent.parent / '.env'
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('GOOGLE_CLIENT_ID='):
                os.environ['GOOGLE_CLIENT_ID'] = line.split('=', 1)[1].strip()
            elif line.startswith('GOOGLE_CLIENT_SECRET='):
                os.environ['GOOGLE_CLIENT_SECRET'] = line.split('=', 1)[1].strip()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-default-key-for-development')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# ALLOWED_HOSTS configuration for Render
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS', '')

if RENDER_EXTERNAL_URL:
    # Use Render provided URL
    ALLOWED_HOSTS = [
        RENDER_EXTERNAL_URL.split('//')[1],
        '.onrender.com',  # All Render domains
        'localhost',
        '127.0.0.1',
    ]
elif ALLOWED_HOSTS_ENV:
    # Use environment variable
    ALLOWED_HOSTS = ALLOWED_HOSTS_ENV.split(',')
else:
    # Local development fallback
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver', '0.0.0.0']

# Application definition

INSTALLED_APPS = [
    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'debug_toolbar',
    'django_crontab',
    'compressor',  # Django-compressor for CSS/JS minification
    'django_celery_beat',  # Celery Beat for scheduled tasks
    'django_celery_results',  # Celery Results backend
    
    # Project apps
    'mobilize.core',
    'mobilize.contacts',
    'mobilize.churches',
    'mobilize.communications',
    'mobilize.tasks',
    'mobilize.authentication',
    'mobilize.admin_panel',
    'mobilize.utils',
    'mobilize.pipeline',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files efficiently
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'mobilize.authentication.middleware.CustomAuthMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mobilize.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'mobilize.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Database configuration with DATABASE_URL support (Render/Supabase)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Parse DATABASE_URL for Render deployment
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    # Fallback to individual environment variables for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'mobilize'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASS', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': 600,  # Connection pooling - keep connections for 10 minutes
            'CONN_HEALTH_CHECKS': True,  # Enable connection health checks
        }
    }

# Custom user model
AUTH_USER_MODEL = 'authentication.User'

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Static file compression and optimization
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

# Whitenoise configuration for efficient static file serving
WHITENOISE_AUTOREFRESH = DEBUG  # Only auto-refresh in development
WHITENOISE_USE_FINDERS = DEBUG  # Use finders in development
WHITENOISE_COMPRESS_OFFLINE = not DEBUG  # Compress static files in production

# Django-compressor settings
COMPRESS_ENABLED = not DEBUG  # Enable compression in production
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.rCSSMinFilter',
]
COMPRESS_JS_FILTERS = ['compressor.filters.jsmin.rJSMinFilter']
COMPRESS_OFFLINE = not DEBUG  # Pre-compress files in production

# Caching Configuration for Performance
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
        'TIMEOUT': 3600,  # 1 hour default timeout
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,  # Fraction of entries that are culled
        },
    }
}

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]

# Authentication settings
AUTHENTICATION_BACKENDS = [
    'mobilize.authentication.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Login URLs
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': os.environ.get('LOG_LEVEL', 'INFO'),
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': os.environ.get('LOG_LEVEL', 'INFO'),
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/mobilize.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'] if os.environ.get('LOG_TO_STDOUT', 'True') == 'True' else ['file'],
        'level': os.environ.get('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Crontab settings for scheduled tasks
CRONJOBS = [
    # Run Supabase synchronization every hour
    ('0 * * * *', 'mobilize.utils.management.commands.sync_supabase.Command.run_from_scheduler', ['--direction=both'], {}, '>> ' + str(BASE_DIR / 'logs/supabase_sync.log') + ' 2>&1'),
    
    # Run Supabase synchronization daily at midnight with full sync
    ('0 0 * * *', 'mobilize.utils.management.commands.sync_supabase.Command.run_from_scheduler', ['--direction=both', '--full'], {}, '>> ' + str(BASE_DIR / 'logs/supabase_sync_full.log') + ' 2>&1'),

    # Generate recurring tasks (e.g., every hour)
    ('0 * * * *', 'mobilize.tasks.management.commands.generate_recurring_tasks.Command', [], {}, '>> ' + str(BASE_DIR / 'logs/generate_recurring_tasks.log') + ' 2>&1'),
]

# Crontab settings
CRONTAB_COMMAND_PREFIX = 'DJANGO_SETTINGS_MODULE=mobilize.settings'

# ============================
# CELERY CONFIGURATION
# ============================

# Celery Configuration Options
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'  # Store results in Django database
CELERY_CACHE_BACKEND = 'django-cache'  # Use Django cache for result caching

# Task serialization
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Timezone configuration
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Task routing and queues
CELERY_TASK_ROUTES = {
    'mobilize.communications.tasks.*': {'queue': 'email'},
    'mobilize.tasks.tasks.*': {'queue': 'notifications'},
    'mobilize.utils.tasks.*': {'queue': 'sync'},
}

# Default queue configuration
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_QUEUES = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'email': {
        'exchange': 'email',
        'routing_key': 'email',
    },
    'notifications': {
        'exchange': 'notifications',
        'routing_key': 'notifications',
    },
    'sync': {
        'exchange': 'sync',
        'routing_key': 'sync',
    },
}

# Task execution configuration
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_ALWAYS_EAGER', 'False') == 'True'  # For testing
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Disable prefetching for better task distribution
CELERY_TASK_ACKS_LATE = True  # Acknowledge tasks after completion
CELERY_WORKER_DISABLE_RATE_LIMITS = False

# Task retry configuration
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 1 minute
CELERY_TASK_MAX_RETRIES = 3

# Beat scheduler configuration (for periodic tasks)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'sync-supabase-hourly': {
        'task': 'mobilize.utils.tasks.sync_supabase_task',
        'schedule': 3600.0,  # Every hour
        'options': {'queue': 'sync'},
    },
    'send-due-date-notifications': {
        'task': 'mobilize.tasks.tasks.send_due_date_notifications',
        'schedule': 1800.0,  # Every 30 minutes
        'options': {'queue': 'notifications'},
    },
    'process-pending-emails': {
        'task': 'mobilize.communications.tasks.process_pending_emails',
        'schedule': 300.0,  # Every 5 minutes
        'options': {'queue': 'email'},
    },
}

# Worker configuration
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True

# Security
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_WORKER_LOG_COLOR = False

# Results backend configuration
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour

# ============================
# TESTING CONFIGURATION
# ============================

# Speed up tests by using in-memory database and simpler password hashing
if 'test' in sys.argv or 'pytest' in sys.modules:
    # Use in-memory SQLite for tests
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
    
    # Use simple password hasher for tests
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
    
    # Disable migrations for faster test setup
    class DisableMigrations:
        def __contains__(self, item):
            return True
        def __getitem__(self, item):
            return None
    
    MIGRATION_MODULES = DisableMigrations()
    
    # Use simple cache for tests
    CACHES['default'] = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
    
    # Make Celery run synchronously in tests
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    
    # Disable compressor in tests
    COMPRESS_ENABLED = False
    
    # Use simple email backend for tests
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
