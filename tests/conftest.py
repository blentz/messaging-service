"""
Pytest configuration and fixtures for the messaging service tests.
"""

import pytest

from app import create_app
from app.config import TestConfig
from app.utils.database import db


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        yield db.session


@pytest.fixture
def auth_headers():
    """Provide authentication headers for API tests."""
    return {"X-API-Key": "api_key_123"}


@pytest.fixture
def admin_headers():
    """Provide admin authentication headers."""
    return {"X-API-Key": "admin_key_789"}


@pytest.fixture
def sample_sms_message():
    """Sample SMS message data for testing."""
    return {
        "from": "+18045551234",
        "to": "+12016661234",
        "type": "sms",
        "body": "Hello from test",
        "timestamp": "2024-11-01T14:00:00Z",
    }


@pytest.fixture
def sample_email_message():
    """Sample email message data for testing."""
    return {
        "from": "test@usehatchapp.com",
        "to": "contact@example.com",
        "body": "Hello from email test",
        "timestamp": "2024-11-01T14:00:00Z",
    }


@pytest.fixture
def sample_sms_webhook():
    """Sample SMS webhook data for testing."""
    return {
        "from": "+18045551234",
        "to": "+12016661234",
        "type": "sms",
        "messaging_provider_id": "test_msg_123",
        "body": "Inbound SMS test",
        "timestamp": "2024-11-01T14:00:00Z",
    }


@pytest.fixture
def sample_email_webhook():
    """Sample email webhook data for testing."""
    return {
        "from": "sender@example.com",
        "to": "test@usehatchapp.com",
        "xillio_id": "test_email_123",
        "body": "<html><body>Inbound email test</body></html>",
        "timestamp": "2024-11-01T14:00:00Z",
    }
