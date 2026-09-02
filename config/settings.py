"""
Django settings for the "Грузинский с нуля" vocabulary trainer.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Set the DJANGO_SECRET_KEY environment variable when deploying.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-me-before-deploying",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")
CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]

# На Render сайт работает за прокси, который сам держит https. Без этой
# строки Django считает соединение небезопасным и отклоняет POST-формы
# (вход, регистрация) с ошибкой про Origin.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "trainer",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
#
# Локально — SQLite, ничего настраивать не нужно.
#
# На сервере обязателен Postgres: на бесплатном тарифе Render файловая
# система пересоздаётся при каждом деплое и перезапуске, и файл SQLite
# вместе с ней — то есть все аккаунты и очки исчезали бы. Render отдаёт
# адрес базы в переменной DATABASE_URL; как только она задана, проект
# сам переключается на неё.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if DATABASE_URL:
    import dj_database_url

    DATABASES["default"] = dj_database_url.parse(
        DATABASE_URL, conn_max_age=600, conn_health_checks=True
    )


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Личный кабинет
LOGIN_URL = "/vhod/"
LOGIN_REDIRECT_URL = "/kabinet/"
LOGOUT_REDIRECT_URL = "/"


LANGUAGE_CODE = "ru"
TIME_ZONE = "Asia/Tbilisi"
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 365  # 1 year — so cumulative score persists
