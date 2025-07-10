"""
Configuration settings for the messaging service.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class."""

    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # Database settings
    DATABASE_URL = (
        os.environ.get("DATABASE_URL")
        or "postgresql://messaging_user:messaging_password@localhost:5432/messaging_service"
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Authentication settings
    AUTH_API_KEY_HEADER = "X-API-Key"
    AUTH_WEBHOOK_SECRET = (
        os.environ.get("WEBHOOK_SECRET") or "webhook-secret-change-in-production"
    )

    # Provider settings
    TWILIO_MOCK_ENABLED = True
    SENDGRID_MOCK_ENABLED = True
    TWILIO_WEBHOOK_SECRET = (
        os.environ.get("TWILIO_WEBHOOK_SECRET") or "twilio-webhook-secret"
    )
    SENDGRID_WEBHOOK_SECRET = (
        os.environ.get("SENDGRID_WEBHOOK_SECRET") or "sendgrid-webhook-secret"
    )

    # Rate limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_PER_MINUTE = 60

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL") or "INFO"
    LOG_FORMAT = "json"

    # OpenTelemetry
    OTEL_METRICS_ENABLED = True
    OTEL_METRICS_PORT = 8081


class TestConfig(Config):
    """Configuration for testing."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    AUTH_WEBHOOK_SECRET = "test-webhook-secret"
    TWILIO_WEBHOOK_SECRET = "test-twilio-secret"
    SENDGRID_WEBHOOK_SECRET = "test-sendgrid-secret"


class DevelopmentConfig(Config):
    """Configuration for development."""

    DEBUG = True


class ProductionConfig(Config):
    """Configuration for production."""

    DEBUG = False
    # Override secrets with environment variables in production
