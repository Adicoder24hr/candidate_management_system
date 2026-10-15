import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY must be configured in the environment.")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_mongodb_backend",
    "apps.candidates",
    "apps.messages_comm",
    "apps.webhooks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
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

# Database Configuration with MongoDB Atlas
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    print("FATAL: MONGODB_URI environment variable is missing in backend/.env", file=sys.stderr)
    sys.exit(1)

DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "NAME": "candidate_comm",
        "HOST": MONGODB_URI,
        "OPTIONS": {},
    }
}

# REST Framework Configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
}

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]

# Internationalization - Set to IST (Asia/Kolkata)
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django_mongodb_backend.fields.ObjectIdAutoField"

# External Provider Configuration
PROVIDER_BASE_URL = os.getenv("PROVIDER_BASE_URL", "http://localhost:8001")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
PROVIDER_WEBHOOK_SECRET = os.getenv("PROVIDER_WEBHOOK_SECRET")
if not PROVIDER_WEBHOOK_SECRET:
    raise RuntimeError("PROVIDER_WEBHOOK_SECRET must be configured in the environment.")

# Database Startup Ping Verification
def verify_db_connection():
    from pymongo import MongoClient
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
        client.admin.command("ping")
        # Ensure default collection exists or can be accessed
        db = client["candidate_comm"]
        _ = db.list_collection_names()
    except Exception as e:
        err_msg = str(e)
        if "@" in err_msg:
            err_msg = err_msg.split("@")[-1]
        print(f"FATAL: Unable to connect to MongoDB Atlas cluster ({type(e).__name__}: {err_msg})", file=sys.stderr)
        # We do not crash hard during migration generation scripts, but warn clearly
        if "migrate" in sys.argv or "runserver" in sys.argv:
            raise

if "runserver" in sys.argv or "test" in sys.argv:
    verify_db_connection()
