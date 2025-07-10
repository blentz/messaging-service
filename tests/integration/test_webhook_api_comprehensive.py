"""
Comprehensive tests for webhook API endpoints to achieve 100% coverage.
"""

import json
import pytest
from unittest.mock import Mock, patch

from app import create_app
from app.config import TestConfig


class TestSMSWebhookAPI:
    """Test SMS webhook API comprehensive coverage."""

    @pytest.fixture
    def app(self):
        return create_app(TestConfig)

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def webhook_headers(self):
        return {
            'X-Twilio-Signature': 'test-signature',
            'Content-Type': 'application/json'
        }

    @patch('app.api.webhooks.validate_webhook_signature')
    @patch('app.api.webhooks.MessageService')
    def test_sms_webhook_json_success(self, mock_message_service, mock_validate_signature, client, webhook_headers):
        """Test successful SMS webhook processing with JSON data."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        # Mock message service
        mock_service = Mock()
        mock_service.process_inbound_sms_webhook.return_value = {"status": "processed", "message_id": 123}
        mock_message_service.return_value = mock_service
        
        webhook_data = {
            "from": "+18045551234",
            "to": "+12016661234",
            "type": "sms",
            "messaging_provider_id": "msg-123",
            "body": "Test SMS webhook"
        }
        
        response = client.post('/api/webhooks/sms', 
                             data=json.dumps(webhook_data),
                             headers=webhook_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "processed"
        assert data["message_id"] == 123
        
        # Verify message service was called
        mock_service.process_inbound_sms_webhook.assert_called_once()

    @patch('app.api.webhooks.validate_webhook_signature')
    @patch('app.api.webhooks.MessageService')
    def test_sms_webhook_form_data_sms(self, mock_message_service, mock_validate_signature, client):
        """Test SMS webhook with form data (Twilio format) - SMS type."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        # Mock message service
        mock_service = Mock()
        mock_service.process_inbound_sms_webhook.return_value = {"status": "processed", "message_id": 124}
        mock_message_service.return_value = mock_service
        
        # Twilio-style form data for SMS (NumMedia = "0")
        form_data = {
            "From": "+18045551234",
            "To": "+12016661234",
            "NumMedia": "0",
            "MessageSid": "SM123456789",
            "Body": "Test SMS via form data",
            "DateCreated": "2025-07-10T10:00:00Z"
        }
        
        headers = {
            'X-Twilio-Signature': 'test-signature',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = client.post('/api/webhooks/sms', 
                             data=form_data,
                             headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "processed"
        assert data["message_id"] == 124
        
        # Verify the form data was converted correctly
        call_args = mock_service.process_inbound_sms_webhook.call_args[0][0]
        assert call_args["from"] == "+18045551234"
        assert call_args["to"] == "+12016661234"
        assert call_args["type"] == "sms"  # Should be SMS because NumMedia = "0"
        assert call_args["messaging_provider_id"] == "SM123456789"
        assert call_args["body"] == "Test SMS via form data"
        assert call_args["timestamp"] == "2025-07-10T10:00:00Z"
        assert call_args["attachments"] == []

    @patch('app.api.webhooks.validate_webhook_signature')
    @patch('app.api.webhooks.MessageService')
    def test_sms_webhook_form_data_mms(self, mock_message_service, mock_validate_signature, client):
        """Test SMS webhook with form data (Twilio format) - MMS type."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        # Mock message service
        mock_service = Mock()
        mock_service.process_inbound_sms_webhook.return_value = {"status": "processed", "message_id": 125}
        mock_message_service.return_value = mock_service
        
        # Twilio-style form data for MMS (NumMedia > "0")
        form_data = {
            "From": "+18045551234",
            "To": "+12016661234",
            "NumMedia": "1",
            "MessageSid": "MM123456789",
            "Body": "Test MMS via form data",
            "MediaUrl0": "https://example.com/image.jpg",
            "DateCreated": "2025-07-10T10:00:00Z"
        }
        
        headers = {
            'X-Twilio-Signature': 'test-signature',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = client.post('/api/webhooks/sms', 
                             data=form_data,
                             headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "processed"
        assert data["message_id"] == 125
        
        # Verify the form data was converted correctly for MMS
        call_args = mock_service.process_inbound_sms_webhook.call_args[0][0]
        assert call_args["type"] == "mms"  # Should be MMS because NumMedia > "0"
        assert call_args["attachments"] == ["https://example.com/image.jpg"]

    @patch('app.api.webhooks.validate_webhook_signature')
    @patch('app.api.webhooks.MessageService')
    def test_sms_webhook_form_data_no_media_url(self, mock_message_service, mock_validate_signature, client):
        """Test SMS webhook form data without MediaUrl0."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        # Mock message service
        mock_service = Mock()
        mock_service.process_inbound_sms_webhook.return_value = {"status": "processed", "message_id": 126}
        mock_message_service.return_value = mock_service
        
        # Twilio-style form data without MediaUrl0
        form_data = {
            "From": "+18045551234",
            "To": "+12016661234",
            "NumMedia": "1",
            "MessageSid": "MM123456789",
            "Body": "Test MMS without media URL"
        }
        
        headers = {
            'X-Twilio-Signature': 'test-signature',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = client.post('/api/webhooks/sms', 
                             data=form_data,
                             headers=headers)
        
        assert response.status_code == 200
        
        # Verify attachments is empty when no MediaUrl0
        call_args = mock_service.process_inbound_sms_webhook.call_args[0][0]
        assert call_args["attachments"] == []

    @patch('app.api.webhooks.validate_webhook_signature')
    def test_sms_webhook_empty_request_body(self, mock_validate_signature, client, webhook_headers):
        """Test SMS webhook with empty request body."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        response = client.post('/api/webhooks/sms', 
                             data=json.dumps(None),
                             headers=webhook_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert "Request body required" in data["error"]

    @patch('app.api.webhooks.validate_webhook_signature')
    @patch('app.api.webhooks.validate_sms_webhook_request')
    def test_sms_webhook_validation_error(self, mock_validate_request, mock_validate_signature, client, webhook_headers):
        """Test SMS webhook with validation error."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        # Mock validation to raise ValueError
        mock_validate_request.side_effect = ValueError("Invalid phone number format")
        
        webhook_data = {
            "from": "invalid-phone",
            "to": "+12016661234",
            "type": "sms",
            "messaging_provider_id": "msg-123",
            "body": "Test SMS webhook"
        }
        
        response = client.post('/api/webhooks/sms', 
                             data=json.dumps(webhook_data),
                             headers=webhook_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid phone number format" in data["error"]

    @patch('app.api.webhooks.validate_webhook_signature')
    @patch('app.api.webhooks.MessageService')
    def test_sms_webhook_service_exception(self, mock_message_service, mock_validate_signature, client, webhook_headers):
        """Test SMS webhook with message service exception."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        # Mock message service to raise exception
        mock_service = Mock()
        mock_service.process_inbound_sms_webhook.side_effect = Exception("Database connection failed")
        mock_message_service.return_value = mock_service
        
        webhook_data = {
            "from": "+18045551234",
            "to": "+12016661234",
            "type": "sms",
            "messaging_provider_id": "msg-123",
            "body": "Test SMS webhook"
        }
        
        response = client.post('/api/webhooks/sms', 
                             data=json.dumps(webhook_data),
                             headers=webhook_headers)
        
        assert response.status_code == 500
        data = response.get_json()
        assert "Internal server error" in data["error"]


class TestEmailWebhookAPI:
    """Test email webhook API comprehensive coverage."""

    @pytest.fixture
    def app(self):
        return create_app(TestConfig)

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def webhook_headers(self):
        return {
            'X-Sendgrid-Signature': 'test-signature',
            'Content-Type': 'application/json'
        }

    @patch('app.api.webhooks.validate_webhook_signature')
    @patch('app.api.webhooks.MessageService')
    def test_email_webhook_success(self, mock_message_service, mock_validate_signature, client, webhook_headers):
        """Test successful email webhook processing."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        # Mock message service
        mock_service = Mock()
        mock_service.process_inbound_email_webhook.return_value = {"status": "processed", "message_id": 201}
        mock_message_service.return_value = mock_service
        
        webhook_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "xillio_id": "email-123",
            "body": "Test email webhook",
            "attachments": ["https://example.com/file.pdf"]
        }
        
        response = client.post('/api/webhooks/email', 
                             data=json.dumps(webhook_data),
                             headers=webhook_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "processed"
        assert data["message_id"] == 201
        
        # Verify message service was called
        mock_service.process_inbound_email_webhook.assert_called_once()

    @patch('app.api.webhooks.validate_webhook_signature')
    def test_email_webhook_empty_json_body(self, mock_validate_signature, client, webhook_headers):
        """Test email webhook with empty JSON body."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        response = client.post('/api/webhooks/email', 
                             data=json.dumps(None),
                             headers=webhook_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert "JSON body required" in data["error"]

    @patch('app.api.webhooks.validate_webhook_signature')
    @patch('app.api.webhooks.validate_email_webhook_request')
    def test_email_webhook_validation_error(self, mock_validate_request, mock_validate_signature, client, webhook_headers):
        """Test email webhook with validation error."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        # Mock validation to raise ValueError
        mock_validate_request.side_effect = ValueError("Invalid email address format")
        
        webhook_data = {
            "from": "invalid-email",
            "to": "recipient@example.com",
            "xillio_id": "email-123",
            "body": "Test email webhook"
        }
        
        response = client.post('/api/webhooks/email', 
                             data=json.dumps(webhook_data),
                             headers=webhook_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid email address format" in data["error"]

    @patch('app.api.webhooks.validate_webhook_signature')
    @patch('app.api.webhooks.MessageService')
    def test_email_webhook_service_exception(self, mock_message_service, mock_validate_signature, client, webhook_headers):
        """Test email webhook with message service exception."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        # Mock message service to raise exception
        mock_service = Mock()
        mock_service.process_inbound_email_webhook.side_effect = Exception("Database connection failed")
        mock_message_service.return_value = mock_service
        
        webhook_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "xillio_id": "email-123",
            "body": "Test email webhook"
        }
        
        response = client.post('/api/webhooks/email', 
                             data=json.dumps(webhook_data),
                             headers=webhook_headers)
        
        assert response.status_code == 500
        data = response.get_json()
        assert "Internal server error" in data["error"]


class TestWebhookAuthenticationHandling:
    """Test webhook authentication error handling."""

    @pytest.fixture
    def app(self):
        return create_app(TestConfig)

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch('app.api.webhooks.validate_webhook_signature')
    def test_sms_webhook_unauthorized(self, mock_validate_signature, client):
        """Test SMS webhook with authentication failure."""
        from werkzeug.exceptions import Unauthorized
        
        # Mock signature validation to raise Unauthorized
        mock_validate_signature.side_effect = Unauthorized("Invalid signature")
        
        webhook_data = {
            "from": "+18045551234",
            "to": "+12016661234",
            "type": "sms",
            "messaging_provider_id": "msg-123",
            "body": "Test SMS webhook"
        }
        
        headers = {
            'X-Twilio-Signature': 'invalid-signature',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/api/webhooks/sms', 
                             data=json.dumps(webhook_data),
                             headers=headers)
        
        assert response.status_code == 401
        data = response.get_json()
        assert "Invalid signature" in data["error"]

    @patch('app.api.webhooks.validate_webhook_signature')
    def test_email_webhook_unauthorized(self, mock_validate_signature, client):
        """Test email webhook with authentication failure."""
        from werkzeug.exceptions import Unauthorized
        
        # Mock signature validation to raise Unauthorized
        mock_validate_signature.side_effect = Unauthorized("Invalid signature")
        
        webhook_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "xillio_id": "email-123",
            "body": "Test email webhook"
        }
        
        headers = {
            'X-Sendgrid-Signature': 'invalid-signature',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/api/webhooks/email', 
                             data=json.dumps(webhook_data),
                             headers=headers)
        
        assert response.status_code == 401
        data = response.get_json()
        assert "Invalid signature" in data["error"]


class TestWebhookMetricsAndLogging:
    """Test webhook metrics and logging functionality."""

    @pytest.fixture
    def app(self):
        return create_app(TestConfig)

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @patch('app.api.webhooks.validate_webhook_signature')
    @patch('app.api.webhooks.MessageService')
    @patch('app.api.webhooks.metrics')
    @patch('app.api.webhooks.logger')
    def test_sms_webhook_metrics_logging(self, mock_logger, mock_metrics, mock_message_service, mock_validate_signature, client):
        """Test SMS webhook metrics and logging."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        # Mock message service
        mock_service = Mock()
        mock_service.process_inbound_sms_webhook.return_value = {"status": "processed", "message_id": 123}
        mock_message_service.return_value = mock_service
        
        webhook_data = {
            "from": "+18045551234",
            "to": "+12016661234",
            "type": "sms",
            "messaging_provider_id": "msg-123",
            "body": "Test SMS webhook"
        }
        
        headers = {
            'X-Twilio-Signature': 'test-signature',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/api/webhooks/sms', 
                             data=json.dumps(webhook_data),
                             headers=headers)
        
        assert response.status_code == 200
        
        # Verify metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify logging
        mock_logger.info.assert_called()

    @patch('app.api.webhooks.validate_webhook_signature')
    @patch('app.api.webhooks.MessageService')
    @patch('app.api.webhooks.metrics')
    @patch('app.api.webhooks.logger')
    def test_email_webhook_metrics_logging(self, mock_logger, mock_metrics, mock_message_service, mock_validate_signature, client):
        """Test email webhook metrics and logging."""
        # Mock signature validation to pass
        mock_validate_signature.return_value = None
        
        # Mock message service
        mock_service = Mock()
        mock_service.process_inbound_email_webhook.return_value = {"status": "processed", "message_id": 201}
        mock_message_service.return_value = mock_service
        
        webhook_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "xillio_id": "email-123",
            "body": "Test email webhook"
        }
        
        headers = {
            'X-Sendgrid-Signature': 'test-signature',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/api/webhooks/email', 
                             data=json.dumps(webhook_data),
                             headers=headers)
        
        assert response.status_code == 200
        
        # Verify metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify logging
        mock_logger.info.assert_called()