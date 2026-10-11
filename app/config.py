"""Settings for each environment: development, testing, production."""
import os

from dotenv import load_dotenv

load_dotenv()


def _database_url():
    """Accept the Neon URL exactly as copied and make it work with the psycopg driver."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _flag(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-secret-change-me"
    SQLALCHEMY_DATABASE_URI = _database_url() or "sqlite:///stocksense-local.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    DEMO_MODE = _flag("DEMO_MODE")
    DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "owner@stocksense.app")
    DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "")
    MAX_CONTENT_LENGTH = 1024 * 1024  # 1 MB upload limit (CSV imports)
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    ALERT_FROM_EMAIL = os.environ.get("ALERT_FROM_EMAIL", "onboarding@resend.dev")
    ALERT_TO_EMAIL = os.environ.get("ALERT_TO_EMAIL", "")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    DEMO_MODE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    name = (name or os.environ.get("APP_ENV") or "development").lower()
    return CONFIGS.get(name, DevelopmentConfig)
