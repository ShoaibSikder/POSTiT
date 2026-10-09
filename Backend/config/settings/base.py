
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def positive_int_setting(name, default):
    value = int(os.environ.get(name, default))
    if value < 1:
        raise ValueError(f"{name} must be a positive integer.")
    return value


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-change-this-before-deployment",
)

DEBUG = False

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "accounts",
    "profiles",
    "posts",
    "comments",
    "likes",
    "follows",
    "feed",
    "search",
    "notifications",
    "audit",
    "moderation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
        "DIRS": [],
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
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTIT_DB_NAME"],
        "USER": os.environ["POSTIT_DB_USER"],
        "PASSWORD": os.environ["POSTIT_DB_PASSWORD"],
        "HOST": os.environ["POSTIT_DB_HOST"],
        "PORT": os.environ["POSTIT_DB_PORT"],
        "CONN_MAX_AGE": 60,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
POSTIT_MAX_IMAGE_SIZE_BYTES = positive_int_setting(
    "POSTIT_MAX_IMAGE_SIZE_BYTES",
    5 * 1024 * 1024,
)
POSTIT_MAX_POST_IMAGES = positive_int_setting("POSTIT_MAX_POST_IMAGES", 5)
POSTIT_MAX_PROFILE_MEDIA = positive_int_setting(
    "POSTIT_MAX_PROFILE_MEDIA",
    10,
)
POSTIT_MAX_POST_LENGTH = positive_int_setting("POSTIT_MAX_POST_LENGTH", 2000)
POSTIT_MAX_COMMENT_LENGTH = positive_int_setting(
    "POSTIT_MAX_COMMENT_LENGTH",
    1000,
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardResultsPagination",
    "PAGE_SIZE": 20,
}