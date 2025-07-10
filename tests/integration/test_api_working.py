"""
Working integration tests for API endpoints.
"""

import json
import pytest

from app import create_app


class TestHealthEndpoint:
    """Test health endpoint."""

    @pytest.fixture
    def app(self):
        return create_app()

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


class TestAuthenticationRequired:
    """Test that protected endpoints require authentication."""

    @pytest.fixture
    def app(self):
        return create_app()

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    def test_sms_endpoint_requires_auth(self, client):
        """Test SMS endpoint requires authentication."""
        data = {"from": "+12016661234", "to": "+18045551234", "type": "sms", "body": "test"}
        response = client.post('/api/messages/sms', 
                             data=json.dumps(data),
                             content_type='application/json')
        assert response.status_code == 401

    def test_email_endpoint_requires_auth(self, client):
        """Test email endpoint requires authentication."""
        data = {"from": "test@example.com", "to": "user@example.com", "body": "test"}
        response = client.post('/api/messages/email',
                             data=json.dumps(data), 
                             content_type='application/json')
        assert response.status_code == 401

    def test_conversations_endpoint_requires_auth(self, client):
        """Test conversations endpoint requires authentication."""
        response = client.get('/api/conversations')
        assert response.status_code == 401

    def test_sms_webhook_requires_auth(self, client):
        """Test SMS webhook requires authentication."""
        data = {"from": "+18045551234", "to": "+12016661234", "type": "sms", "body": "test"}
        response = client.post('/api/webhooks/sms',
                             data=json.dumps(data),
                             content_type='application/json')
        assert response.status_code == 401

    def test_email_webhook_requires_auth(self, client):
        """Test email webhook requires authentication."""
        data = {"from": "test@example.com", "to": "user@example.com", "body": "test"}
        response = client.post('/api/webhooks/email',
                             data=json.dumps(data),
                             content_type='application/json')
        assert response.status_code == 401


class TestAuthenticatedEndpoints:
    """Test endpoints with valid authentication."""

    @pytest.fixture
    def app(self):
        return create_app()

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def auth_headers(self):
        return {'X-API-Key': 'admin_key_789', 'Content-Type': 'application/json'}

    def test_conversations_with_auth(self, client, auth_headers):
        """Test conversations endpoint with valid auth."""
        response = client.get('/api/conversations', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'conversations' in data