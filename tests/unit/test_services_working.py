"""
Working unit tests for service layer.
"""

import pytest
from unittest.mock import Mock, patch

from app import create_app
from app.config import TestConfig
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.services.provider_service import ProviderService


class TestConversationService:
    """Test conversation service."""

    @pytest.fixture
    def app(self):
        return create_app(TestConfig)

    def test_service_initialization(self, app):
        """Test service initializes correctly."""
        with app.app_context():
            service = ConversationService()
            assert service is not None

    @patch('app.models.conversation.Conversation.query')
    def test_get_conversations(self, mock_query, app):
        """Test getting conversations."""
        with app.app_context():
            service = ConversationService()
            # Mock the query chain
            mock_query.count.return_value = 0
            mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            
            conversations, total = service.get_conversations()
            assert conversations == []
            assert total == 0


class TestMessageService:
    """Test message service."""

    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = MessageService()
        assert service is not None

    @patch('app.services.provider_service.ProviderService.send_sms_message')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    @patch('app.services.conversation_service.ConversationService.add_message_to_conversation')
    @patch('app.utils.database.db.session')
    def test_send_sms_message(self, mock_db_session, mock_add_message, mock_conversation, mock_provider):
        """Test sending SMS message."""
        service = MessageService()
        mock_conversation.return_value = Mock(id=1)
        mock_provider.return_value = {"sid": "msg-123", "status": "sent"}
        
        result = service.send_sms_message(
            from_address="+12016661234",
            to_address="+18045551234", 
            message_type="sms",
            body="test"
        )
        assert result is not None
        assert "message_id" in result


class TestProviderService:
    """Test provider service."""

    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = ProviderService()
        assert service is not None