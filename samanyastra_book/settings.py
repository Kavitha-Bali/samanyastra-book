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
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"]) + [".samanyastra.com"]
CSRF_TRUSTED_ORIGINS = ["https://*.samanyastra.com"]

# The k8s ingress terminates TLS and forwards plain HTTP to this pod, so Django
# must be told to trust X-Forwarded-Proto — otherwise request.is_secure() is
# always False, reset-link emails are built as http://, and the CSRF Origin
# check compares against the wrong scheme.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

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
    'sso_integration',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "sso_integration.middleware.JWTCookieMiddleware",
    # Gates every view behind request.user.is_authenticated by default.
    # Views that must stay public opt out with @login_not_required.
    # Must run after JWTCookieMiddleware so it sees the JWT-resolved user.
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
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
        "NAME":     env("DB_NAME",     default=""),
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
TIME_ZONE = "Asia/Kolkata"
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
RAZORPAY_KEY_ID     = env("RAZORPAY_KEY",    default="")
RAZORPAY_KEY_SECRET = env("RAZORPAY_SECRET", default="")

# ── Outlook ──────────────────────────────────────────────────
OUTLOOK_TENANT_ID     = env("OUTLOOK_TENANT_ID",     default="")
OUTLOOK_CLIENT_ID     = env("OUTLOOK_CLIENT_ID",     default="")
OUTLOOK_CLIENT_SECRET = env("OUTLOOK_CLIENT_SECRET", default="")

# Not used for actual Celery config anywhere — the vendored django_messaging
# package's __init__.py does a hard `is None` check on this setting at import
# time even though its OutlookBackend sends mail synchronously via requests.
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="not-used")

# ── Mail Service ──────────────────────────────────────────────
MAIL_SERVICE_URL        = env("MAIL_SERVICE_URL", default="http://127.0.0.1:8000")
MAIL_SERVICE_APP_ID     = env("MAIL_SERVICE_APP_ID", default="")
MAIL_SERVICE_APP_SECRET = env("MAIL_SERVICE_APP_SECRET", default="")
MAIL_SERVICE_FROM_EMAIL = env("DEFAULT_FROM_MAIL", default="noreply@samanyastra.com")



# ── Logging ──────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "DEBUG" if DEBUG else "ERROR"},
    "loggers": {
        "django":             {"handlers": ["console"], "level": "DEBUG" if DEBUG else "ERROR", "propagate": False},
        "django.request":     {"handlers": ["console"], "level": "DEBUG" if DEBUG else "ERROR", "propagate": False},
        "django.template":    {"handlers": ["console"], "level": "DEBUG" if DEBUG else "ERROR", "propagate": False},
        "django.db.backends": {"handlers": ["console"], "level": "DEBUG" if DEBUG else "ERROR", "propagate": False},
    },
}

# ── Azure Storage (media + static) ────────────────────────────
AZURE_ACCOUNT_NAME      = env("AZURE_ACCOUNT_NAME",      default="")
AZURE_ACCOUNT_KEY       = env("AZURE_ACCOUNT_KEY",       default="")
AZURE_CONNECTION_STRING = env("AZURE_CONNECTION_STRING", default="")
AZURE_CONTAINER_MEDIA   = "media"
AZURE_CONTAINER_STATIC  = "static"

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
        "BACKEND": "books.storage.ProxiedAzureStaticStorage",
        "OPTIONS": {
            "azure_container": AZURE_CONTAINER_STATIC,
            "account_name": AZURE_ACCOUNT_NAME,
            "account_key": AZURE_ACCOUNT_KEY,
            "connection_string": AZURE_CONNECTION_STRING,
        },
    },
}


# SSO Integration
# Defaults must never be None: sso_integration.views.callback_view does
# `redirect(next_url or settings.LOGIN_REDIRECT_URL)` with no None-check,
# so a missing env var here crashes the callback for any user who logs in
# without a `?next=` (i.e. anyone who didn't get bounced off a protected page).
LOGIN_URL =  "/login/"
LOGIN_REDIRECT_URL ="/shop/"

# Samanyastra Auth integration
SAMANYASTRA_AUTH_URL = env("SAMANYASTRA_AUTH_URL")
SAMANYASTRA_APP_ID = env("SAMANYASTRA_APP_ID")
SAMANYASTRA_APP_SECRET = env("SAMANYASTRA_APP_SECRET")
SAMANYASTRA_REDIRECT_URI = env("SAMANYASTRA_REDIRECT_URI")

# Local JWT settings
JWT_SECRET = env("JWT_SECRET")
JWT_ACCESS_EXPIRE_MINUTES = env.int("JWT_ACCESS_EXPIRE_MINUTES", default=15)
JWT_REFRESH_EXPIRE_DAYS = env.int("JWT_REFRESH_EXPIRE_DAYS", default=7)