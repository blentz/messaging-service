"""
Comprehensive tests for message API endpoints to achieve 100% coverage.
"""

import json
import pytest
from unittest.mock import Mock, patch

from app import create_app
from app.config import TestConfig
from app.providers.base import ProviderError


class TestMessageAPIErrorHandling:
    """Test message API error handling comprehensive coverage."""

    @pytest.fixture
    def app(self):
        return create_app(TestConfig)

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def auth_headers(self):
        return {'X-API-Key': 'admin_key_789', 'Content-Type': 'application/json'}

    @patch('app.api.messages.validate_sms_message_request')
    def test_sms_message_validation_error(self, mock_validate_request, client, auth_headers):
        """Test SMS message with validation error."""
        # Mock validation to raise ValueError
        mock_validate_request.side_effect = ValueError("Invalid phone number format")
        
        message_data = {
            "from": "invalid-phone",
            "to": "+18045551234",
            "type": "sms",
            "body": "Test SMS message"
        }
        
        response = client.post('/api/messages/sms', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid phone number format" in data["error"]

    @patch('app.api.messages.MessageService')
    def test_sms_message_provider_error(self, mock_message_service, client, auth_headers):
        """Test SMS message with provider error."""
        # Mock message service to raise ProviderError
        mock_service = Mock()
        mock_service.send_sms_message.side_effect = ProviderError("Provider service unavailable", 503)
        mock_message_service.return_value = mock_service
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "Test SMS message"
        }
        
        response = client.post('/api/messages/sms', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 503
        data = response.get_json()
        assert "Provider service unavailable" in data["error"]

    @patch('app.api.messages.MessageService')
    def test_sms_message_general_exception(self, mock_message_service, client, auth_headers):
        """Test SMS message with general exception."""
        # Mock message service to raise general exception
        mock_service = Mock()
        mock_service.send_sms_message.side_effect = Exception("Database connection failed")
        mock_message_service.return_value = mock_service
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "Test SMS message"
        }
        
        response = client.post('/api/messages/sms', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 500
        data = response.get_json()
        assert "Internal server error" in data["error"]

    def test_email_message_empty_json_body(self, client, auth_headers):
        """Test email message with empty JSON body."""
        response = client.post('/api/messages/email', 
                             data=json.dumps(None),
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert "JSON body required" in data["error"]

    @patch('app.api.messages.validate_email_message_request')
    def test_email_message_validation_error(self, mock_validate_request, client, auth_headers):
        """Test email message with validation error."""
        # Mock validation to raise ValueError
        mock_validate_request.side_effect = ValueError("Invalid email address format")
        
        message_data = {
            "from": "invalid-email",
            "to": "recipient@example.com",
            "body": "Test email message"
        }
        
        response = client.post('/api/messages/email', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid email address format" in data["error"]

    @patch('app.api.messages.MessageService')
    def test_email_message_provider_error(self, mock_message_service, client, auth_headers):
        """Test email message with provider error."""
        # Mock message service to raise ProviderError
        mock_service = Mock()
        mock_service.send_email_message.side_effect = ProviderError("Email service quota exceeded", 429)
        mock_message_service.return_value = mock_service
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": "Test email message"
        }
        
        response = client.post('/api/messages/email', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 429
        data = response.get_json()
        assert "Email service quota exceeded" in data["error"]

    @patch('app.api.messages.MessageService')
    def test_email_message_general_exception(self, mock_message_service, client, auth_headers):
        """Test email message with general exception."""
        # Mock message service to raise general exception
        mock_service = Mock()
        mock_service.send_email_message.side_effect = Exception("Internal service error")
        mock_message_service.return_value = mock_service
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": "Test email message"
        }
        
        response = client.post('/api/messages/email', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 500
        data = response.get_json()
        assert "Internal server error" in data["error"]


class TestMessageAPIMetricsAndLogging:
    """Test message API metrics and logging functionality."""

    @pytest.fixture
    def app(self):
        return create_app(TestConfig)

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def auth_headers(self):
        return {'X-API-Key': 'admin_key_789', 'Content-Type': 'application/json'}

    @patch('app.api.messages.MessageService')
    @patch('app.api.messages.metrics')
    @patch('app.api.messages.logger')
    def test_sms_message_success_metrics_logging(self, mock_logger, mock_metrics, mock_message_service, client, auth_headers):
        """Test SMS message success metrics and logging."""
        # Mock message service
        mock_service = Mock()
        mock_service.send_sms_message.return_value = {
            "message_id": 123,
            "status": "sent",
            "conversation_id": 456,
            "sent_at": "2025-07-10T10:00:00Z"
        }
        mock_message_service.return_value = mock_service
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "Test SMS message"
        }
        
        response = client.post('/api/messages/sms', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify logging
        mock_logger.info.assert_called()

    @patch('app.api.messages.MessageService')
    @patch('app.api.messages.metrics')
    @patch('app.api.messages.logger')
    def test_email_message_success_metrics_logging(self, mock_logger, mock_metrics, mock_message_service, client, auth_headers):
        """Test email message success metrics and logging."""
        # Mock message service
        mock_service = Mock()
        mock_service.send_email_message.return_value = {
            "message_id": 124,
            "status": "sent",
            "conversation_id": 457,
            "sent_at": "2025-07-10T10:05:00Z"
        }
        mock_message_service.return_value = mock_service
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": "Test email message"
        }
        
        response = client.post('/api/messages/email', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify logging
        mock_logger.info.assert_called()

    @patch('app.api.messages.validate_sms_message_request')
    @patch('app.api.messages.metrics')
    @patch('app.api.messages.logger')
    def test_sms_validation_error_metrics_logging(self, mock_logger, mock_metrics, mock_validate_request, client, auth_headers):
        """Test SMS validation error metrics and logging."""
        # Mock validation to raise ValueError
        mock_validate_request.side_effect = ValueError("Invalid message format")
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "Test SMS message"
        }
        
        response = client.post('/api/messages/sms', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        
        # Verify error metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify warning was logged
        mock_logger.warning.assert_called()

    @patch('app.api.messages.MessageService')
    @patch('app.api.messages.metrics')
    @patch('app.api.messages.logger')
    def test_sms_provider_error_metrics_logging(self, mock_logger, mock_metrics, mock_message_service, client, auth_headers):
        """Test SMS provider error metrics and logging."""
        # Mock message service to raise ProviderError
        mock_service = Mock()
        mock_service.send_sms_message.side_effect = ProviderError("Provider error", 400)
        mock_message_service.return_value = mock_service
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "Test SMS message"
        }
        
        response = client.post('/api/messages/sms', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        
        # Verify error metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify warning was logged
        mock_logger.warning.assert_called()

    @patch('app.api.messages.MessageService')
    @patch('app.api.messages.metrics')
    @patch('app.api.messages.logger')
    def test_sms_general_error_metrics_logging(self, mock_logger, mock_metrics, mock_message_service, client, auth_headers):
        """Test SMS general error metrics and logging."""
        # Mock message service to raise general exception
        mock_service = Mock()
        mock_service.send_sms_message.side_effect = Exception("General error")
        mock_message_service.return_value = mock_service
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "Test SMS message"
        }
        
        response = client.post('/api/messages/sms', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 500
        
        # Verify error metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify error was logged
        mock_logger.error.assert_called()

    @patch('app.api.messages.validate_email_message_request')
    @patch('app.api.messages.metrics')
    @patch('app.api.messages.logger')
    def test_email_validation_error_metrics_logging(self, mock_logger, mock_metrics, mock_validate_request, client, auth_headers):
        """Test email validation error metrics and logging."""
        # Mock validation to raise ValueError
        mock_validate_request.side_effect = ValueError("Invalid email format")
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": "Test email message"
        }
        
        response = client.post('/api/messages/email', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        
        # Verify error metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify warning was logged
        mock_logger.warning.assert_called()

    @patch('app.api.messages.MessageService')
    @patch('app.api.messages.metrics')
    @patch('app.api.messages.logger')
    def test_email_provider_error_metrics_logging(self, mock_logger, mock_metrics, mock_message_service, client, auth_headers):
        """Test email provider error metrics and logging."""
        # Mock message service to raise ProviderError
        mock_service = Mock()
        mock_service.send_email_message.side_effect = ProviderError("Provider error", 400)
        mock_message_service.return_value = mock_service
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": "Test email message"
        }
        
        response = client.post('/api/messages/email', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        
        # Verify error metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify warning was logged
        mock_logger.warning.assert_called()

    @patch('app.api.messages.MessageService')
    @patch('app.api.messages.metrics')
    @patch('app.api.messages.logger')
    def test_email_general_error_metrics_logging(self, mock_logger, mock_metrics, mock_message_service, client, auth_headers):
        """Test email general error metrics and logging."""
        # Mock message service to raise general exception
        mock_service = Mock()
        mock_service.send_email_message.side_effect = Exception("General error")
        mock_message_service.return_value = mock_service
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": "Test email message"
        }
        
        response = client.post('/api/messages/email', 
                             data=json.dumps(message_data),
                             headers=auth_headers)
        
        assert response.status_code == 500
        
        # Verify error metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify error was logged
        mock_logger.error.assert_called()