from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env (silently skipped in Docker build where .env is intentionally absent)
env = environ.Env(
    DEBUG=(bool, False),
)
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(_env_file)

# ── Secrets ──────────────────────────────────────────────────
SECRET_KEY = env("SECRET_KEY", default="insecure-build-placeholder")
DEBUG = False
ALLOWED_HOSTS      = env.list("ALLOWED_HOSTS", default=[]) + [".samanyastra.com"]
CSRF_TRUSTED_ORIGINS = ["https://*.samanyastra.com"]

# ── Applications ─────────────────────────────────────────────
INSTALLED_APPS = [
     "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "books",
    "rest_framework",
    "django_messaging",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "samanyastra_book.urls"

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

WSGI_APPLICATION = "samanyastra_book.wsgi.application"

# ── Database ──────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     env("BOOKS_DB_NAME",     default=""),
        "USER":     env("DB_USER",     default=""),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST":     env("DB_HOST",     default=""),
        "PORT":     env("DB_PORT",     default="5432"),
    }
}

# ── Password validation ───────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internationalisation ──────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static / Media ────────────────────────────────────────────
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT  = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Messages ──────────────────────────────────────────────────
from django.contrib.messages import constants as message_constants

MESSAGE_TAGS = {
    message_constants.DEBUG: "info",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "error",
}

# ── REST Framework ────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
}

# ── Razorpay ──────────────────────────────────────────────────
RAZORPAY_KEY_ID     = env("RAZORPAY_KEY_ID",     default="")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET", default="")

# ── Outlook ──────────────────────────────────────────────────
OUTLOOK_TENANT_ID     = env("OUTLOOK_TENANT_ID",     default="")
OUTLOOK_CLIENT_ID     = env("OUTLOOK_CLIENT_ID",     default="")
OUTLOOK_CLIENT_SECRET = env("OUTLOOK_CLIENT_SECRET", default="")

# ── Celery ────────────────────────────────────────────────────
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="")
CELERY_TIMEZONE   = TIME_ZONE



# ── Azure Storage (media only) ────────────────────────────────
AZURE_ACCOUNT_NAME      = env("AZURE_ACCOUNT_NAME",      default="")
AZURE_ACCOUNT_KEY       = env("AZURE_ACCOUNT_KEY",       default="")
AZURE_CONNECTION_STRING = env("AZURE_CONNECTION_STRING", default="")
AZURE_CONTAINER_MEDIA   = "media"

MEDIA_URL = "/media/"

STORAGES = {
    "default": {
        "BACKEND": "books.storage.ProxiedAzureStorage",
        "OPTIONS": {
            "azure_container": AZURE_CONTAINER_MEDIA,
            "account_name": AZURE_ACCOUNT_NAME,
            "account_key": AZURE_ACCOUNT_KEY,
            "connection_string": AZURE_CONNECTION_STRING,
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}