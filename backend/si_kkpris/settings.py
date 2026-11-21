"""
Django settings for si_kkpris project.
Sistem Informasi Pembiayaan dan Koperasi Syariah (SI-KKPRIS)
Koperasi KKPRIS SMK Negeri 1 Kota Solok
"""

import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BACKEND_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = BACKEND_DIR
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / 'frontend'

# Load environment variables from .env (utamakan backend/.env, fallback ke root implementasi)
_env_path = BACKEND_DIR / '.env'
if not _env_path.exists():
    _env_path = PROJECT_ROOT / '.env'
load_dotenv(_env_path)

def _env_bool(nama: str, default: bool = False, getter=os.getenv) -> bool:
    nilai = getter(nama)
    if nilai is None or nilai.strip() == '':
        return default
    return nilai.strip().lower() in ('true', '1', 'yes')


def _resolusi_konfigurasi_keamanan(getter=os.getenv) -> dict:
    debug = _env_bool('DEBUG', default=False, getter=getter)
    secret_key = (getter('SECRET_KEY') or '').strip()
    if not secret_key:
        raise ImproperlyConfigured(
            'Environment variable SECRET_KEY wajib diatur di environment atau backend/.env.'
        )
    default_https = not debug
    return {
        'DEBUG': debug,
        'SECRET_KEY': secret_key,
        'SESSION_COOKIE_SECURE': _env_bool(
            'SESSION_COOKIE_SECURE', default=default_https, getter=getter
        ),
        'CSRF_COOKIE_SECURE': _env_bool(
            'CSRF_COOKIE_SECURE', default=default_https, getter=getter
        ),
        'SECURE_SSL_REDIRECT': _env_bool(
            'SECURE_SSL_REDIRECT', default=default_https, getter=getter
        ),
    }


# SECURITY WARNING: keep the secret key used in production secret!
# SECURITY WARNING: don't run with debug turned on in production!
_keamanan = _resolusi_konfigurasi_keamanan()
DEBUG = _keamanan['DEBUG']
SECRET_KEY = _keamanan['SECRET_KEY']
SESSION_COOKIE_SECURE = _keamanan['SESSION_COOKIE_SECURE']
CSRF_COOKIE_SECURE = _keamanan['CSRF_COOKIE_SECURE']
SECURE_SSL_REDIRECT = _keamanan['SECURE_SSL_REDIRECT']
TRUSTED_PROXY = _env_bool('TRUSTED_PROXY', default=False)

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
    if host.strip()
]

# Aturan bisnis sementara
# PENDING PND-01: margin contoh, BUKAN ketetapan koperasi. Satuan sementara: persen dari pokok
# PER BULAN (flat). Dipakai bila pengajuan tidak menyertakan margin_persen.
try:
    MARGIN_PERSEN_SEMENTARA = Decimal(
        os.getenv('MARGIN_PERSEN_SEMENTARA') or '1.00'
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
except InvalidOperation as exc:
    raise ImproperlyConfigured(
        'MARGIN_PERSEN_SEMENTARA harus berupa angka desimal, contoh: 1.00'
    ) from exc

# Password awal untuk management command seed_master (dibaca dari env, tidak ditulis di kode)
SEED_PASSWORD = os.getenv('SEED_PASSWORD', '').strip()

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Aplikasi Utama SI-KKPRIS (16 Model 3NF & MVT Controllers)
    'koperasi.apps.KoperasiConfig',
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

ROOT_URLCONF = 'si_kkpris.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [FRONTEND_DIR / 'templates'],
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

WSGI_APPLICATION = 'si_kkpris.wsgi.application'

# Database Configuration — MySQL 8.0+ (InnoDB, utf8mb4_unicode_ci)
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.mysql'),
        'NAME': os.getenv('DB_NAME', 'si_kkpris'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Password validation & Hashing (PBKDF2 SHA256 saja sesuai NFR Security & AGENTS.md 4.F)
AUTH_PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

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

# Internationalization (Bahasa Indonesia & Waktu Indonesia Barat)
LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = False

# Session Security (FR-AUTH-03: Session Timeout Otomatis 30 Menit)
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [FRONTEND_DIR / 'static']
STATIC_ROOT = BACKEND_DIR / 'staticfiles'

# Media Uploads (Berkas KTP, Agunan, Bukti Transfer, Surat Resign)
MEDIA_URL = 'media/'
MEDIA_ROOT = BACKEND_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
