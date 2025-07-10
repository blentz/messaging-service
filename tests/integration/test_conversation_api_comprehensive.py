"""
Comprehensive tests for conversation API endpoints to achieve 100% coverage.
"""

import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app import create_app
from app.config import TestConfig


class TestConversationsAPI:
    """Test conversations API comprehensive coverage."""

    @pytest.fixture
    def app(self):
        return create_app(TestConfig)

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def auth_headers(self):
        return {'X-API-Key': 'admin_key_789', 'Content-Type': 'application/json'}

    @patch('app.api.conversations.ConversationService')
    def test_get_conversations_success(self, mock_conversation_service, client, auth_headers):
        """Test successful conversations retrieval."""
        # Mock conversation service
        mock_service = Mock()
        mock_conversations = [
            Mock(to_dict=Mock(return_value={
                "id": 1,
                "participants": ["+18045551234", "+12016661234"],
                "conversation_type": "sms_mms",
                "created_at": "2025-07-10T10:00:00Z",
                "updated_at": "2025-07-10T11:00:00Z",
                "last_message_at": "2025-07-10T11:00:00Z",
                "message_count": 5,
                "metadata": {}
            })),
            Mock(to_dict=Mock(return_value={
                "id": 2,
                "participants": ["sender@example.com", "recipient@example.com"],
                "conversation_type": "email",
                "created_at": "2025-07-10T09:00:00Z",
                "updated_at": "2025-07-10T10:00:00Z",
                "last_message_at": "2025-07-10T10:00:00Z",
                "message_count": 3,
                "metadata": {}
            }))
        ]
        mock_service.get_conversations.return_value = (mock_conversations, 2)
        mock_conversation_service.return_value = mock_service
        
        response = client.get('/api/conversations?limit=25&offset=0', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 2
        assert data["limit"] == 25
        assert data["offset"] == 0
        assert len(data["conversations"]) == 2
        assert data["conversations"][0]["id"] == 1
        assert data["conversations"][1]["id"] == 2
        
        # Verify service was called with correct parameters
        mock_service.get_conversations.assert_called_once_with(
            limit=25, offset=0, search=None
        )

    @patch('app.api.conversations.ConversationService')
    def test_get_conversations_with_search(self, mock_conversation_service, client, auth_headers):
        """Test conversations retrieval with search parameter."""
        # Mock conversation service
        mock_service = Mock()
        mock_conversations = [
            Mock(to_dict=Mock(return_value={
                "id": 1,
                "participants": ["+18045551234", "+12016661234"],
                "conversation_type": "sms_mms",
                "created_at": "2025-07-10T10:00:00Z",
                "updated_at": "2025-07-10T11:00:00Z",
                "last_message_at": "2025-07-10T11:00:00Z",
                "message_count": 5,
                "metadata": {}
            }))
        ]
        mock_service.get_conversations.return_value = (mock_conversations, 1)
        mock_conversation_service.return_value = mock_service
        
        response = client.get('/api/conversations?search=%2B18045551234', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 1
        assert len(data["conversations"]) == 1
        
        # Verify service was called with search parameter  
        mock_service.get_conversations.assert_called_once_with(
            limit=50, offset=0, search='+18045551234'  # URL encoded %2B becomes +
        )

    @patch('app.api.conversations.ConversationService')
    def test_get_conversations_default_pagination(self, mock_conversation_service, client, auth_headers):
        """Test conversations retrieval with default pagination."""
        # Mock conversation service
        mock_service = Mock()
        mock_service.get_conversations.return_value = ([], 0)
        mock_conversation_service.return_value = mock_service
        
        response = client.get('/api/conversations', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["limit"] == 50  # Default limit
        assert data["offset"] == 0   # Default offset
        
        # Verify service was called with defaults
        mock_service.get_conversations.assert_called_once_with(
            limit=50, offset=0, search=None
        )

    @patch('app.api.conversations.validate_pagination_params')
    def test_get_conversations_validation_error(self, mock_validate_pagination, client, auth_headers):
        """Test conversations retrieval with validation error."""
        # Mock validation to raise ValueError
        mock_validate_pagination.side_effect = ValueError("Limit must be between 1 and 1000")
        
        response = client.get('/api/conversations?limit=2000', headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert "Limit must be between 1 and 1000" in data["error"]

    @patch('app.api.conversations.ConversationService')
    def test_get_conversations_service_exception(self, mock_conversation_service, client, auth_headers):
        """Test conversations retrieval with service exception."""
        # Mock service to raise exception
        mock_service = Mock()
        mock_service.get_conversations.side_effect = Exception("Database connection failed")
        mock_conversation_service.return_value = mock_service
        
        response = client.get('/api/conversations', headers=auth_headers)
        
        assert response.status_code == 500
        data = response.get_json()
        assert "Internal server error" in data["error"]

    @patch('app.api.conversations.ConversationService')
    @patch('app.api.conversations.metrics')
    @patch('app.api.conversations.logger')
    def test_get_conversations_metrics_logging(self, mock_logger, mock_metrics, mock_conversation_service, client, auth_headers):
        """Test conversations retrieval metrics and logging."""
        # Mock conversation service
        mock_service = Mock()
        mock_conversations = [Mock(to_dict=Mock(return_value={"id": 1}))]
        mock_service.get_conversations.return_value = (mock_conversations, 1)
        mock_conversation_service.return_value = mock_service
        
        response = client.get('/api/conversations', headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify logging
        mock_logger.info.assert_called()


class TestConversationMessagesAPI:
    """Test conversation messages API comprehensive coverage."""

    @pytest.fixture
    def app(self):
        return create_app(TestConfig)

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def auth_headers(self):
        return {'X-API-Key': 'admin_key_789', 'Content-Type': 'application/json'}

    @patch('app.api.conversations.ConversationService')
    def test_get_conversation_messages_success(self, mock_conversation_service, client, auth_headers):
        """Test successful conversation messages retrieval."""
        # Mock conversation service
        mock_service = Mock()
        mock_messages = [
            Mock(to_dict=Mock(return_value={
                "id": 1,
                "conversation_id": 123,
                "from": "+18045551234",
                "to": "+12016661234",
                "type": "sms",
                "direction": "outbound",
                "body": "Hello world",
                "attachments": [],
                "provider_id": "twilio_123",
                "provider_name": "twilio_mock",
                "status": "sent",
                "created_at": "2025-07-10T10:00:00Z",
                "updated_at": "2025-07-10T10:00:00Z",
                "sent_at": "2025-07-10T10:00:00Z"
            })),
            Mock(to_dict=Mock(return_value={
                "id": 2,
                "conversation_id": 123,
                "from": "+12016661234",
                "to": "+18045551234",
                "type": "sms",
                "direction": "inbound",
                "body": "Hello back!",
                "attachments": [],
                "provider_id": "twilio_456",
                "provider_name": "twilio_mock",
                "status": "delivered",
                "created_at": "2025-07-10T10:05:00Z",
                "updated_at": "2025-07-10T10:05:00Z",
                "sent_at": "2025-07-10T10:05:00Z"
            }))
        ]
        mock_service.get_conversation_messages.return_value = (mock_messages, 2)
        mock_conversation_service.return_value = mock_service
        
        response = client.get('/api/conversations/123/messages?limit=25&offset=0', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 2
        assert data["limit"] == 25
        assert data["offset"] == 0
        assert data["conversation_id"] == 123
        assert len(data["messages"]) == 2
        assert data["messages"][0]["id"] == 1
        assert data["messages"][1]["id"] == 2
        
        # Verify service was called with correct parameters
        mock_service.get_conversation_messages.assert_called_once_with(
            conversation_id=123, limit=25, offset=0, since=None
        )

    @patch('app.api.conversations.ConversationService')
    def test_get_conversation_messages_with_since(self, mock_conversation_service, client, auth_headers):
        """Test conversation messages retrieval with since parameter."""
        # Mock conversation service
        mock_service = Mock()
        mock_messages = [
            Mock(to_dict=Mock(return_value={
                "id": 2,
                "conversation_id": 123,
                "from": "+12016661234",
                "to": "+18045551234",
                "type": "sms",
                "direction": "inbound",
                "body": "Recent message",
                "attachments": [],
                "provider_id": "twilio_456",
                "provider_name": "twilio_mock",
                "status": "delivered",
                "created_at": "2025-07-10T11:00:00Z",
                "updated_at": "2025-07-10T11:00:00Z",
                "sent_at": "2025-07-10T11:00:00Z"
            }))
        ]
        mock_service.get_conversation_messages.return_value = (mock_messages, 1)
        mock_conversation_service.return_value = mock_service
        
        since_timestamp = "2025-07-10T10:30:00Z"
        response = client.get(f'/api/conversations/123/messages?since={since_timestamp}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 1
        assert len(data["messages"]) == 1
        
        # Verify service was called with since parameter
        mock_service.get_conversation_messages.assert_called_once_with(
            conversation_id=123, limit=50, offset=0, since=since_timestamp
        )

    @patch('app.api.conversations.ConversationService')
    def test_get_conversation_messages_default_pagination(self, mock_conversation_service, client, auth_headers):
        """Test conversation messages retrieval with default pagination."""
        # Mock conversation service
        mock_service = Mock()
        mock_service.get_conversation_messages.return_value = ([], 0)
        mock_conversation_service.return_value = mock_service
        
        response = client.get('/api/conversations/456/messages', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["limit"] == 50  # Default limit
        assert data["offset"] == 0   # Default offset
        assert data["conversation_id"] == 456
        
        # Verify service was called with defaults
        mock_service.get_conversation_messages.assert_called_once_with(
            conversation_id=456, limit=50, offset=0, since=None
        )

    @patch('app.api.conversations.validate_pagination_params')
    def test_get_conversation_messages_validation_error(self, mock_validate_pagination, client, auth_headers):
        """Test conversation messages retrieval with validation error."""
        # Mock validation to raise ValueError
        mock_validate_pagination.side_effect = ValueError("Offset must be non-negative")
        
        response = client.get('/api/conversations/123/messages?offset=-1', headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert "Offset must be non-negative" in data["error"]

    @patch('app.api.conversations.ConversationService')
    def test_get_conversation_messages_service_exception(self, mock_conversation_service, client, auth_headers):
        """Test conversation messages retrieval with service exception."""
        # Mock service to raise exception
        mock_service = Mock()
        mock_service.get_conversation_messages.side_effect = Exception("Conversation not found")
        mock_conversation_service.return_value = mock_service
        
        response = client.get('/api/conversations/999/messages', headers=auth_headers)
        
        assert response.status_code == 500
        data = response.get_json()
        assert "Internal server error" in data["error"]

    @patch('app.api.conversations.ConversationService')
    @patch('app.api.conversations.metrics')
    @patch('app.api.conversations.logger')
    def test_get_conversation_messages_metrics_logging(self, mock_logger, mock_metrics, mock_conversation_service, client, auth_headers):
        """Test conversation messages retrieval metrics and logging."""
        # Mock conversation service
        mock_service = Mock()
        mock_messages = [Mock(to_dict=Mock(return_value={"id": 1, "conversation_id": 123}))]
        mock_service.get_conversation_messages.return_value = (mock_messages, 1)
        mock_conversation_service.return_value = mock_service
        
        response = client.get('/api/conversations/123/messages', headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify logging
        mock_logger.info.assert_called()

    @patch('app.api.conversations.ConversationService')
    def test_get_conversation_messages_complex_pagination(self, mock_conversation_service, client, auth_headers):
        """Test conversation messages with complex pagination scenario."""
        # Mock conversation service
        mock_service = Mock()
        mock_messages = []
        for i in range(10):
            mock_messages.append(Mock(to_dict=Mock(return_value={
                "id": i + 1,
                "conversation_id": 123,
                "from": "+18045551234",
                "to": "+12016661234",
                "type": "sms",
                "direction": "outbound",
                "body": f"Message {i + 1}",
                "attachments": [],
                "provider_id": f"twilio_{i + 1}",
                "provider_name": "twilio_mock",
                "status": "sent",
                "created_at": f"2025-07-10T10:{i:02d}:00Z",
                "updated_at": f"2025-07-10T10:{i:02d}:00Z",
                "sent_at": f"2025-07-10T10:{i:02d}:00Z"
            })))
        
        mock_service.get_conversation_messages.return_value = (mock_messages, 100)  # 100 total, returning 10
        mock_conversation_service.return_value = mock_service
        
        response = client.get('/api/conversations/123/messages?limit=10&offset=20', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 100
        assert data["limit"] == 10
        assert data["offset"] == 20
        assert data["conversation_id"] == 123
        assert len(data["messages"]) == 10
        
        # Verify service was called with correct pagination
        mock_service.get_conversation_messages.assert_called_once_with(
            conversation_id=123, limit=10, offset=20, since=None
        )


class TestConversationAPIErrorHandling:
    """Test conversation API error handling scenarios."""

    @pytest.fixture
    def app(self):
        return create_app(TestConfig)

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def auth_headers(self):
        return {'X-API-Key': 'admin_key_789', 'Content-Type': 'application/json'}

    @patch('app.api.conversations.ConversationService')
    @patch('app.api.conversations.metrics')
    @patch('app.api.conversations.logger')
    def test_conversations_validation_error_metrics(self, mock_logger, mock_metrics, mock_conversation_service, client, auth_headers):
        """Test conversations validation error metrics and logging."""
        with patch('app.api.conversations.validate_pagination_params') as mock_validate:
            mock_validate.side_effect = ValueError("Invalid pagination parameters")
            
            response = client.get('/api/conversations?limit=invalid', headers=auth_headers)
            
            assert response.status_code == 400
            
            # Verify error metrics were recorded
            mock_metrics.increment_counter.assert_called()
            mock_metrics.record_histogram.assert_called()
            
            # Verify warning was logged
            mock_logger.warning.assert_called()

    @patch('app.api.conversations.ConversationService')
    @patch('app.api.conversations.metrics')
    @patch('app.api.conversations.logger')
    def test_conversations_service_error_metrics(self, mock_logger, mock_metrics, mock_conversation_service, client, auth_headers):
        """Test conversations service error metrics and logging."""
        # Mock service to raise exception
        mock_service = Mock()
        mock_service.get_conversations.side_effect = Exception("Internal service error")
        mock_conversation_service.return_value = mock_service
        
        response = client.get('/api/conversations', headers=auth_headers)
        
        assert response.status_code == 500
        
        # Verify error metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify error was logged
        mock_logger.error.assert_called()

    @patch('app.api.conversations.ConversationService')
    @patch('app.api.conversations.metrics')
    @patch('app.api.conversations.logger')
    def test_conversation_messages_validation_error_metrics(self, mock_logger, mock_metrics, mock_conversation_service, client, auth_headers):
        """Test conversation messages validation error metrics and logging."""
        with patch('app.api.conversations.validate_pagination_params') as mock_validate:
            mock_validate.side_effect = ValueError("Invalid pagination parameters")
            
            response = client.get('/api/conversations/123/messages?limit=invalid', headers=auth_headers)
            
            assert response.status_code == 400
            
            # Verify error metrics were recorded
            mock_metrics.increment_counter.assert_called()
            mock_metrics.record_histogram.assert_called()
            
            # Verify warning was logged with conversation_id
            mock_logger.warning.assert_called()

    @patch('app.api.conversations.ConversationService')
    @patch('app.api.conversations.metrics')
    @patch('app.api.conversations.logger')
    def test_conversation_messages_service_error_metrics(self, mock_logger, mock_metrics, mock_conversation_service, client, auth_headers):
        """Test conversation messages service error metrics and logging."""
        # Mock service to raise exception
        mock_service = Mock()
        mock_service.get_conversation_messages.side_effect = Exception("Conversation service error")
        mock_conversation_service.return_value = mock_service
        
        response = client.get('/api/conversations/456/messages', headers=auth_headers)
        
        assert response.status_code == 500
        
        # Verify error metrics were recorded
        mock_metrics.increment_counter.assert_called()
        mock_metrics.record_histogram.assert_called()
        
        # Verify error was logged with conversation_id
        mock_logger.error.assert_called()