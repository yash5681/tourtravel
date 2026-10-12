"""
Django settings for delux_travel project.
Configured for Full-Stack Delux Tour & Travel with WAMP MySQL.
"""

from pathlib import Path
import os
import pymysql

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

# Patch MySQLdb with pymysql for WAMP MySQL support
pymysql.install_as_MySQLdb()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'delux-tour-travel-super-secret-key-wamp-mysql-django-2026')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '*').split(',') if h.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tours',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'delux_travel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'delux_travel.wsgi.application'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Ensure directories exist
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

# Database configuration: WAMP Server MySQL with auto-creation & SQLite fallback
def _configure_database():
    import socket
    mysql_host = '127.0.0.1'
    mysql_port = 3306
    db_name = 'deluxtourtraveldb'

    # Check if MySQL server port 3306 is reachable
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.5)
    is_mysql_running = (sock.connect_ex((mysql_host, mysql_port)) == 0)
    sock.close()

    if is_mysql_running:
        try:
            # Auto-ensure database exists on MySQL
            conn = pymysql.connect(host=mysql_host, port=mysql_port, user='root', password='', charset='utf8mb4')
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.close()
        except Exception:
            pass

        return {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': db_name,
                'USER': 'root',
                'PASSWORD': '',
                'HOST': mysql_host,
                'PORT': str(mysql_port),
                'OPTIONS': {
                    'charset': 'utf8mb4',
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES', NAMES utf8mb4",
                },
                'TEST': {
                    'CHARSET': 'utf8mb4',
                    'COLLATION': 'utf8mb4_unicode_ci',
                }
            }
        }
    else:
        # Fallback to local SQLite database if WAMP is stopped
        return {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

DATABASES = _configure_database()

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Session configuration
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days
SESSION_SAVE_EVERY_REQUEST = True

# Admin default credentials
ADMIN_CREDENTIALS = {
    'email': 'admin@deluxtour.com',
    'password': 'Admin@123'
}

# Email notification configuration (Gmail SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_TIMEOUT = 5  # Prevent SMTP network hangs
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'yashprajapati5681@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'psnt rycn gkuh rrur')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'pyash7571@gmail.com')
ADMIN_NOTIFY_EMAIL = os.getenv('ADMIN_NOTIFY_EMAIL', 'yashprajapati5681@gmail.com')

# Direct UPI Payment Gateway Configuration
TOUR_UPI_ID = os.getenv('TOUR_UPI_ID', 'deluxtour@upi')
TOUR_UPI_PAYEE_NAME = os.getenv('TOUR_UPI_PAYEE_NAME', 'Delux Tour and Travel')
TOUR_UPI_NOTE_PREFIX = os.getenv('TOUR_UPI_NOTE_PREFIX', 'DeluxTour')
TOUR_UPI_CURRENCY = 'INR'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
