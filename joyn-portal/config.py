import os
from datetime import timedelta


class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET', 'dev-jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_COOKIE_NAME = 'joyn_session'
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'data/portal.db')
    JOYN_PORTAL_SECRET = os.environ.get('JOYN_PORTAL_SECRET', '')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'hire@tryjoyn.me')
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    # Iris agent backend (for 5V health data)
    IRIS_AGENT_URL = os.environ.get('IRIS_AGENT_URL', '')
    IRIS_INTERNAL_KEY = os.environ.get('IRIS_INTERNAL_KEY', '')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class TestingConfig(BaseConfig):
    TESTING = True
    DATABASE_PATH = ':memory:'
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    def validate(self):
        required = ['SECRET_KEY', 'JWT_SECRET_KEY', 'JOYN_PORTAL_SECRET']
        missing = [k for k in required if not os.environ.get(k)]
        if missing:
            raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")


_configs = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}


def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return _configs.get(env, DevelopmentConfig)()
