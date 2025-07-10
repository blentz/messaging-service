"""
Comprehensive unit tests for ConversationService to achieve 100% coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app import create_app
from app.config import TestConfig
from app.services.conversation_service import ConversationService
from app.models.conversation import Conversation, ConversationType
from app.models.message import Message, MessageType


class TestConversationService:
    """Comprehensive test suite for ConversationService."""

    @pytest.fixture
    def app(self):
        return create_app(TestConfig)

    @pytest.fixture
    def conversation_service(self):
        return ConversationService()

    def test_service_initialization(self, conversation_service):
        """Test service initializes correctly."""
        assert conversation_service is not None
        assert conversation_service.logger is not None
        assert conversation_service.metrics is not None

    @patch('app.services.conversation_service.db.session')
    @patch('app.services.conversation_service.log_message_event')
    @patch('app.services.conversation_service.Conversation.find_by_participants')
    @patch('app.services.conversation_service.Conversation')
    def test_find_or_create_conversation_new(
        self, mock_conversation_class, mock_find_by_participants, mock_log_event, mock_db_session, conversation_service
    ):
        """Test creating a new conversation when none exists."""
        # Setup mocks
        mock_find_by_participants.return_value = None
        mock_conversation = Mock()
        mock_conversation.id = 123
        mock_conversation_class.return_value = mock_conversation
        
        result = conversation_service.find_or_create_conversation(
            from_address="+12016661234",
            to_address="+18045551234",
            message_type=MessageType.SMS
        )
        
        # Verify result
        assert result == mock_conversation
        
        # Verify conversation was created with sorted participants
        mock_conversation_class.assert_called_once_with(
            participants=["+12016661234", "+18045551234"],
            conversation_type=ConversationType.SMS_MMS
        )
        
        # Verify database operations
        mock_db_session.add.assert_called_once_with(mock_conversation)
        mock_db_session.commit.assert_called_once()
        
        # Verify logging and metrics
        mock_log_event.assert_called_once()

    @patch('app.models.conversation.Conversation.find_by_participants')
    def test_find_or_create_conversation_existing(
        self, mock_find_by_participants, conversation_service
    ):
        """Test finding an existing conversation."""
        # Setup mock conversation
        mock_conversation = Mock()
        mock_conversation.id = 456
        mock_find_by_participants.return_value = mock_conversation
        
        with patch.object(conversation_service, '_update_conversation_type') as mock_update:
            result = conversation_service.find_or_create_conversation(
                from_address="+12016661234",
                to_address="+18045551234",
                message_type=MessageType.EMAIL
            )
            
            # Verify result
            assert result == mock_conversation
            
            # Verify participants are sorted for consistent lookup
            mock_find_by_participants.assert_called_once_with(["+12016661234", "+18045551234"])
            
            # Verify conversation type update was attempted
            mock_update.assert_called_once_with(mock_conversation, MessageType.EMAIL)

    @patch('app.models.conversation.Conversation.query')
    def test_get_conversations_no_search(self, mock_query, conversation_service):
        """Test getting conversations without search filter."""
        # Setup mock query chain
        mock_conversations = [Mock(), Mock()]
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_conversations
        
        conversations, total = conversation_service.get_conversations(limit=10, offset=0)
        
        assert conversations == mock_conversations
        assert total == 2
        
        # Verify query was built correctly
        mock_query.count.assert_called_once()
        mock_query.order_by.assert_called_once()

    @patch('app.models.conversation.Conversation.query')
    def test_get_conversations_with_search(self, mock_query, conversation_service):
        """Test getting conversations with search filter."""
        # Setup mock query chain
        mock_conversations = [Mock()]
        mock_filtered_query = Mock()
        mock_query.filter.return_value = mock_filtered_query
        mock_filtered_query.count.return_value = 1
        mock_filtered_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_conversations
        
        conversations, total = conversation_service.get_conversations(
            limit=10, offset=0, search="+12016661234"
        )
        
        assert conversations == mock_conversations
        assert total == 1
        
        # Verify search filter was applied
        mock_query.filter.assert_called_once()

    @patch('app.models.message.Message.query')
    def test_get_conversation_messages_no_since(self, mock_query, conversation_service):
        """Test getting conversation messages without since filter."""
        # Setup mock query chain
        mock_messages = [Mock(), Mock(), Mock()]
        mock_filtered_query = Mock()
        mock_query.filter_by.return_value = mock_filtered_query
        mock_filtered_query.count.return_value = 3
        mock_filtered_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_messages
        
        messages, total = conversation_service.get_conversation_messages(
            conversation_id=123, limit=20, offset=0
        )
        
        assert messages == mock_messages
        assert total == 3
        
        # Verify query was built correctly
        mock_query.filter_by.assert_called_once_with(conversation_id=123)

    @patch('app.models.message.Message.query')
    def test_get_conversation_messages_with_valid_since(self, mock_query, conversation_service):
        """Test getting conversation messages with valid since timestamp."""
        # Setup mock query chain
        mock_messages = [Mock()]
        mock_filtered_query = Mock()
        mock_query.filter_by.return_value = mock_filtered_query
        mock_since_filtered_query = Mock()
        mock_filtered_query.filter.return_value = mock_since_filtered_query
        mock_since_filtered_query.count.return_value = 1
        mock_since_filtered_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_messages
        
        messages, total = conversation_service.get_conversation_messages(
            conversation_id=123, limit=20, offset=0, since="2023-01-01T12:00:00Z"
        )
        
        assert messages == mock_messages
        assert total == 1
        
        # Verify since filter was applied
        mock_filtered_query.filter.assert_called_once()

    @patch('app.models.message.Message.query')
    def test_get_conversation_messages_with_invalid_since(self, mock_query, conversation_service):
        """Test getting conversation messages with invalid since timestamp."""
        # Setup mock query chain
        mock_messages = [Mock()]
        mock_filtered_query = Mock()
        mock_query.filter_by.return_value = mock_filtered_query
        mock_filtered_query.count.return_value = 1
        mock_filtered_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_messages
        
        with patch.object(conversation_service.logger, 'warning') as mock_warning:
            messages, total = conversation_service.get_conversation_messages(
                conversation_id=123, limit=20, offset=0, since="invalid_timestamp"
            )
            
            # Should still return results, just log warning
            assert messages == mock_messages
            assert total == 1
            
            # Verify warning was logged
            mock_warning.assert_called_once_with(
                "Invalid since timestamp format", since="invalid_timestamp"
            )

    @patch('app.services.conversation_service.db.session')
    @patch('app.services.conversation_service.log_message_event')
    def test_add_message_to_conversation(
        self, mock_log_event, mock_db_session, conversation_service
    ):
        """Test adding a message to a conversation."""
        # Setup mocks
        mock_conversation = Mock()
        mock_conversation.id = 789
        mock_message = Mock()
        mock_message.id = 101112
        mock_message.message_type = MessageType.SMS
        
        with patch.object(conversation_service, '_update_conversation_type') as mock_update:
            conversation_service.add_message_to_conversation(mock_conversation, mock_message)
            
            # Verify message was associated with conversation
            assert mock_message.conversation_id == 789
            mock_conversation.add_message.assert_called_once()
            
            # Verify conversation type update was attempted
            mock_update.assert_called_once_with(mock_conversation, MessageType.SMS)
            
            # Verify database commit
            mock_db_session.commit.assert_called_once()
            
            # Verify logging
            mock_log_event.assert_called_once_with(
                "message_added_to_conversation",
                conversation_id=789,
                message_id=101112,
                message_type="sms",
            )

    def test_determine_conversation_type_sms(self, conversation_service):
        """Test determining conversation type for SMS."""
        result = conversation_service._determine_conversation_type(MessageType.SMS)
        assert result == ConversationType.SMS_MMS

    def test_determine_conversation_type_mms(self, conversation_service):
        """Test determining conversation type for MMS."""
        result = conversation_service._determine_conversation_type(MessageType.MMS)
        assert result == ConversationType.SMS_MMS

    def test_determine_conversation_type_email(self, conversation_service):
        """Test determining conversation type for email."""
        result = conversation_service._determine_conversation_type(MessageType.EMAIL)
        assert result == ConversationType.EMAIL

    @patch('app.services.conversation_service.log_message_event')
    def test_update_conversation_type_to_mixed(self, mock_log_event, conversation_service):
        """Test updating conversation type to mixed when different types are used."""
        # Setup mock conversation with SMS type
        mock_conversation = Mock()
        mock_conversation.id = 999
        mock_conversation.conversation_type = ConversationType.SMS_MMS
        
        # Add email message to SMS conversation
        conversation_service._update_conversation_type(mock_conversation, MessageType.EMAIL)
        
        # Verify conversation type was updated to mixed
        assert mock_conversation.conversation_type == ConversationType.MIXED
        
        # Verify logging
        mock_log_event.assert_called_once_with(
            "conversation_type_updated_to_mixed",
            conversation_id=999,
            previous_type="sms_mms",
            new_message_type="email",
        )

    def test_update_conversation_type_same_type(self, conversation_service):
        """Test updating conversation type when message type is same."""
        # Setup mock conversation with SMS type
        mock_conversation = Mock()
        mock_conversation.conversation_type = ConversationType.SMS_MMS
        
        # Add SMS message to SMS conversation
        conversation_service._update_conversation_type(mock_conversation, MessageType.SMS)
        
        # Verify conversation type remains unchanged
        assert mock_conversation.conversation_type == ConversationType.SMS_MMS

    def test_update_conversation_type_already_mixed(self, conversation_service):
        """Test updating conversation type when already mixed."""
        # Setup mock conversation with mixed type
        mock_conversation = Mock()
        mock_conversation.conversation_type = ConversationType.MIXED
        
        # Add any message to mixed conversation
        conversation_service._update_conversation_type(mock_conversation, MessageType.EMAIL)
        
        # Verify conversation type remains mixed
        assert mock_conversation.conversation_type == ConversationType.MIXED

    @patch('app.services.conversation_service.db.session')
    @patch('app.services.conversation_service.log_message_event')
    @patch('app.services.conversation_service.Conversation.find_by_participants')
    @patch('app.services.conversation_service.Conversation')
    def test_find_or_create_conversation_email_type(
        self, mock_conversation_class, mock_find_by_participants, mock_log_event, mock_db_session, conversation_service
    ):
        """Test creating a new conversation for email message type."""
        # Setup mocks
        mock_find_by_participants.return_value = None
        mock_conversation = Mock()
        mock_conversation.id = 789
        mock_conversation_class.return_value = mock_conversation
        
        result = conversation_service.find_or_create_conversation(
            from_address="user@example.com",
            to_address="contact@example.com",
            message_type=MessageType.EMAIL
        )
        
        # Verify conversation was created with EMAIL type
        mock_conversation_class.assert_called_once_with(
            participants=["contact@example.com", "user@example.com"],  # sorted
            conversation_type=ConversationType.EMAIL
        )

    @patch('app.services.conversation_service.db.session')
    @patch('app.services.conversation_service.log_message_event')
    @patch('app.services.conversation_service.Conversation.find_by_participants')
    @patch('app.services.conversation_service.Conversation')
    def test_find_or_create_conversation_mms_type(
        self, mock_conversation_class, mock_find_by_participants, mock_log_event, mock_db_session, conversation_service
    ):
        """Test creating a new conversation for MMS message type."""
        # Setup mocks
        mock_find_by_participants.return_value = None
        mock_conversation = Mock()
        mock_conversation.id = 101
        mock_conversation_class.return_value = mock_conversation
        
        result = conversation_service.find_or_create_conversation(
            from_address="+12016661234",
            to_address="+18045551234",
            message_type=MessageType.MMS
        )
        
        # Verify conversation was created with SMS_MMS type (both SMS and MMS use same type)
        mock_conversation_class.assert_called_once_with(
            participants=["+12016661234", "+18045551234"],
            conversation_type=ConversationType.SMS_MMS
        )