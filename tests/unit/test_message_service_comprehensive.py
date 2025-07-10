"""
Comprehensive unit tests for MessageService to achieve 100% coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app import create_app
from app.config import TestConfig
from app.services.message_service import MessageService
from app.models.message import MessageType, MessageDirection, MessageStatus, ProviderName
from app.providers.base import ProviderError


class TestMessageService:
    """Comprehensive test suite for MessageService."""

    @pytest.fixture
    def app(self):
        return create_app(TestConfig)

    @pytest.fixture
    def message_service(self):
        return MessageService()

    def test_service_initialization(self, message_service):
        """Test service initializes correctly."""
        assert message_service is not None
        assert message_service.logger is not None
        assert message_service.metrics is not None
        assert message_service.conversation_service is not None
        assert message_service.provider_service is not None

    @patch('app.services.message_service.time.time')
    @patch('app.services.message_service.db.session')
    @patch('app.services.message_service.log_message_event')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    @patch('app.services.conversation_service.ConversationService.add_message_to_conversation')
    @patch('app.services.provider_service.ProviderService.send_sms_message')
    def test_send_sms_message_success(
        self, mock_provider, mock_add_message, mock_find_conversation, 
        mock_log_event, mock_db_session, mock_time, message_service
    ):
        """Test successful SMS message sending."""
        # Setup mocks
        mock_time.return_value = 1000.0
        mock_conversation = Mock(id=1)
        mock_find_conversation.return_value = mock_conversation
        mock_provider.return_value = {"sid": "SM123456", "status": "sent"}
        
        # Create a mock message that will be created
        mock_message = Mock()
        mock_message.id = "msg-123"
        mock_message.status = Mock(value="sent")
        mock_message.sent_at = datetime.utcnow()
        
        with patch('app.services.message_service.Message') as mock_message_class:
            mock_message_class.return_value = mock_message
            
            result = message_service.send_sms_message(
                from_address="+12016661234",
                to_address="+18045551234",
                message_type="sms",
                body="Test SMS message"
            )
            
            # Verify result
            assert result["message_id"] == "msg-123"
            assert result["status"] == "sent"
            assert result["conversation_id"] == 1
            assert "sent_at" in result
            
            # Verify method calls
            mock_find_conversation.assert_called_once()
            mock_add_message.assert_called_once()
            mock_provider.assert_called_once()
            mock_message.mark_sent.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @patch('app.services.message_service.time.time')
    @patch('app.services.message_service.db.session')
    @patch('app.services.message_service.log_message_event')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    @patch('app.services.conversation_service.ConversationService.add_message_to_conversation')
    @patch('app.services.provider_service.ProviderService.send_sms_message')
    def test_send_mms_message_with_attachments(
        self, mock_provider, mock_add_message, mock_find_conversation,
        mock_log_event, mock_db_session, mock_time, message_service
    ):
        """Test successful MMS message sending with attachments."""
        # Setup mocks
        mock_time.return_value = 1000.0
        mock_conversation = Mock(id=2)
        mock_find_conversation.return_value = mock_conversation
        mock_provider.return_value = {"sid": "MM123456", "status": "sent"}
        
        mock_message = Mock()
        mock_message.id = "msg-456"
        mock_message.status = Mock(value="sent")
        mock_message.sent_at = datetime.utcnow()
        
        with patch('app.services.message_service.Message') as mock_message_class:
            mock_message_class.return_value = mock_message
            
            result = message_service.send_sms_message(
                from_address="+12016661234",
                to_address="+18045551234",
                message_type="mms",
                body="Test MMS message",
                attachments=["https://example.com/image.jpg"],
                timestamp="2023-01-01T12:00:00Z"
            )
            
            # Verify MMS type handling
            assert result["message_id"] == "msg-456"
            
            # Verify provider was called with attachments and timestamp
            call_args = mock_provider.call_args[0][0]
            assert call_args["attachments"] == ["https://example.com/image.jpg"]
            assert call_args["timestamp"] == "2023-01-01T12:00:00Z"

    @patch('app.services.message_service.time.time')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    @patch('app.services.conversation_service.ConversationService.add_message_to_conversation')
    @patch('app.services.provider_service.ProviderService.send_sms_message')
    def test_send_sms_message_provider_error(self, mock_provider, mock_add_message, mock_find_conversation, mock_time, message_service):
        """Test SMS message sending with provider error."""
        mock_time.return_value = 1000.0
        mock_find_conversation.return_value = Mock(id=1)
        mock_add_message.return_value = None
        mock_provider.side_effect = ProviderError("Provider unavailable", 503)
        
        with patch('app.services.message_service.Message') as mock_message_class:
            mock_message_class.return_value = Mock()
            
            with pytest.raises(ProviderError):
                message_service.send_sms_message(
                    from_address="+12016661234",
                    to_address="+18045551234",
                    message_type="sms",
                    body="Test message"
                )

    @patch('app.services.message_service.time.time')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    def test_send_sms_message_general_exception(self, mock_find_conversation, mock_time, message_service):
        """Test SMS message sending with general exception."""
        mock_time.return_value = 1000.0
        mock_find_conversation.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            message_service.send_sms_message(
                from_address="+12016661234",
                to_address="+18045551234",
                message_type="sms",
                body="Test message"
            )

    @patch('app.services.message_service.time.time')
    @patch('app.services.message_service.db.session')
    @patch('app.services.message_service.log_message_event')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    @patch('app.services.conversation_service.ConversationService.add_message_to_conversation')
    @patch('app.services.provider_service.ProviderService.send_email_message')
    def test_send_email_message_success(
        self, mock_provider, mock_add_message, mock_find_conversation,
        mock_log_event, mock_db_session, mock_time, message_service
    ):
        """Test successful email message sending."""
        # Setup mocks
        mock_time.return_value = 1000.0
        mock_conversation = Mock(id=3)
        mock_find_conversation.return_value = mock_conversation
        mock_provider.return_value = {"message_id": "email-123", "status": "sent"}
        
        mock_message = Mock()
        mock_message.id = "msg-789"
        mock_message.status = Mock(value="sent")
        mock_message.sent_at = datetime.utcnow()
        
        with patch('app.services.message_service.Message') as mock_message_class:
            mock_message_class.return_value = mock_message
            
            result = message_service.send_email_message(
                from_address="sender@example.com",
                to_address="recipient@example.com",
                body="Test email message"
            )
            
            # Verify result
            assert result["message_id"] == "msg-789"
            assert result["status"] == "sent"
            assert result["conversation_id"] == 3
            assert "sent_at" in result
            
            # Verify message was created with correct type
            mock_message_class.assert_called_once()
            call_kwargs = mock_message_class.call_args[1]
            assert call_kwargs["message_type"] == MessageType.EMAIL
            assert call_kwargs["direction"] == MessageDirection.OUTBOUND

    @patch('app.services.message_service.time.time')
    @patch('app.services.message_service.db.session')
    @patch('app.services.message_service.log_message_event')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    @patch('app.services.conversation_service.ConversationService.add_message_to_conversation')
    @patch('app.services.provider_service.ProviderService.send_email_message')
    def test_send_email_message_with_attachments(
        self, mock_provider, mock_add_message, mock_find_conversation,
        mock_log_event, mock_db_session, mock_time, message_service
    ):
        """Test email message sending with attachments."""
        mock_time.return_value = 1000.0
        mock_conversation = Mock(id=4)
        mock_find_conversation.return_value = mock_conversation
        mock_provider.return_value = {"message_id": "email-456", "status": "sent"}
        
        mock_message = Mock()
        mock_message.id = "msg-101"
        mock_message.status = Mock(value="sent")
        mock_message.sent_at = datetime.utcnow()
        
        with patch('app.services.message_service.Message') as mock_message_class:
            mock_message_class.return_value = mock_message
            
            result = message_service.send_email_message(
                from_address="sender@example.com",
                to_address="recipient@example.com",
                body="<h1>HTML Email</h1>",
                attachments=["https://example.com/document.pdf"],
                timestamp="2023-01-01T15:00:00Z"
            )
            
            assert result["message_id"] == "msg-101"
            
            # Verify provider was called with attachments and timestamp
            call_args = mock_provider.call_args[0][0]
            assert call_args["attachments"] == ["https://example.com/document.pdf"]
            assert call_args["timestamp"] == "2023-01-01T15:00:00Z"

    @patch('app.services.message_service.time.time')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    @patch('app.services.conversation_service.ConversationService.add_message_to_conversation')
    @patch('app.services.provider_service.ProviderService.send_email_message')
    def test_send_email_message_provider_error(self, mock_provider, mock_add_message, mock_find_conversation, mock_time, message_service):
        """Test email message sending with provider error."""
        mock_time.return_value = 1000.0
        mock_find_conversation.return_value = Mock(id=1)
        mock_add_message.return_value = None
        mock_provider.side_effect = ProviderError("SendGrid rate limit", 429)
        
        with patch('app.services.message_service.Message') as mock_message_class:
            mock_message_class.return_value = Mock()
            
            with pytest.raises(ProviderError):
                message_service.send_email_message(
                    from_address="sender@example.com",
                    to_address="recipient@example.com",
                    body="Test email"
                )

    @patch('app.services.message_service.time.time')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    def test_send_email_message_general_exception(self, mock_find_conversation, mock_time, message_service):
        """Test email message sending with general exception."""
        mock_time.return_value = 1000.0
        mock_find_conversation.side_effect = Exception("Email validation error")
        
        with pytest.raises(Exception, match="Email validation error"):
            message_service.send_email_message(
                from_address="sender@example.com",
                to_address="recipient@example.com",
                body="Test email"
            )

    @patch('app.services.message_service.time.time')
    @patch('app.services.message_service.log_message_event')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    @patch('app.services.conversation_service.ConversationService.add_message_to_conversation')
    def test_process_inbound_sms_webhook_success(
        self, mock_add_message, mock_find_conversation, mock_log_event, mock_time, message_service
    ):
        """Test successful inbound SMS webhook processing."""
        mock_time.return_value = 1000.0
        mock_conversation = Mock(id=5)
        mock_find_conversation.return_value = mock_conversation
        
        mock_message = Mock()
        mock_message.id = "msg-webhook-123"
        
        webhook_data = {
            "from": "+18045551234",
            "to": "+12016661234",
            "type": "sms",
            "messaging_provider_id": "SM987654",
            "body": "Inbound SMS message",
            "attachments": []
        }
        
        with patch('app.services.message_service.Message') as mock_message_class:
            mock_message_class.return_value = mock_message
            
            result = message_service.process_inbound_sms_webhook(webhook_data)
            
            assert result["status"] == "processed"
            assert result["message_id"] == "msg-webhook-123"
            
            # Verify message was created with correct attributes
            mock_message_class.assert_called_once()
            call_kwargs = mock_message_class.call_args[1]
            assert call_kwargs["message_type"] == MessageType.SMS
            assert call_kwargs["direction"] == MessageDirection.INBOUND
            assert call_kwargs["provider_name"] == ProviderName.TWILIO_MOCK
            assert call_kwargs["status"] == MessageStatus.DELIVERED

    @patch('app.services.message_service.time.time')
    @patch('app.services.message_service.log_message_event')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    @patch('app.services.conversation_service.ConversationService.add_message_to_conversation')
    def test_process_inbound_mms_webhook_with_attachments(
        self, mock_add_message, mock_find_conversation, mock_log_event, mock_time, message_service
    ):
        """Test inbound MMS webhook processing with attachments."""
        mock_time.return_value = 1000.0
        mock_conversation = Mock(id=6)
        mock_find_conversation.return_value = mock_conversation
        
        mock_message = Mock()
        mock_message.id = "msg-mms-webhook"
        
        webhook_data = {
            "from": "+18045551234",
            "to": "+12016661234",
            "type": "mms",
            "messaging_provider_id": "MM987654",
            "body": "Check out this image!",
            "attachments": ["https://provider.com/media/image.jpg"]
        }
        
        with patch('app.services.message_service.Message') as mock_message_class:
            mock_message_class.return_value = mock_message
            
            result = message_service.process_inbound_sms_webhook(webhook_data)
            
            assert result["status"] == "processed"
            
            # Verify MMS type and attachments
            call_kwargs = mock_message_class.call_args[1]
            assert call_kwargs["message_type"] == MessageType.MMS
            assert call_kwargs["attachments"] == ["https://provider.com/media/image.jpg"]

    @patch('app.services.message_service.time.time')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    def test_process_inbound_sms_webhook_exception(self, mock_find_conversation, mock_time, message_service):
        """Test inbound SMS webhook processing with exception."""
        mock_time.return_value = 1000.0
        mock_find_conversation.side_effect = Exception("Webhook processing error")
        
        webhook_data = {
            "from": "+18045551234",
            "to": "+12016661234",
            "type": "sms",
            "messaging_provider_id": "SM987654",
            "body": "Test message"
        }
        
        with pytest.raises(Exception, match="Webhook processing error"):
            message_service.process_inbound_sms_webhook(webhook_data)

    @patch('app.services.message_service.time.time')
    @patch('app.services.message_service.log_message_event')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    @patch('app.services.conversation_service.ConversationService.add_message_to_conversation')
    def test_process_inbound_email_webhook_success(
        self, mock_add_message, mock_find_conversation, mock_log_event, mock_time, message_service
    ):
        """Test successful inbound email webhook processing."""
        mock_time.return_value = 1000.0
        mock_conversation = Mock(id=7)
        mock_find_conversation.return_value = mock_conversation
        
        mock_message = Mock()
        mock_message.id = "msg-email-webhook"
        
        webhook_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "xillio_id": "email-123456",
            "body": "Inbound email message",
            "attachments": ["https://provider.com/attachment.pdf"]
        }
        
        with patch('app.services.message_service.Message') as mock_message_class:
            mock_message_class.return_value = mock_message
            
            result = message_service.process_inbound_email_webhook(webhook_data)
            
            assert result["status"] == "processed"
            assert result["message_id"] == "msg-email-webhook"
            
            # Verify message was created with correct attributes
            mock_message_class.assert_called_once()
            call_kwargs = mock_message_class.call_args[1]
            assert call_kwargs["message_type"] == MessageType.EMAIL
            assert call_kwargs["direction"] == MessageDirection.INBOUND
            assert call_kwargs["provider_name"] == ProviderName.SENDGRID_MOCK
            assert call_kwargs["status"] == MessageStatus.DELIVERED
            assert call_kwargs["provider_id"] == "email-123456"

    @patch('app.services.message_service.time.time')
    @patch('app.services.conversation_service.ConversationService.find_or_create_conversation')
    def test_process_inbound_email_webhook_exception(self, mock_find_conversation, mock_time, message_service):
        """Test inbound email webhook processing with exception."""
        mock_time.return_value = 1000.0
        mock_find_conversation.side_effect = Exception("Email webhook error")
        
        webhook_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "xillio_id": "email-123456",
            "body": "Test email"
        }
        
        with pytest.raises(Exception, match="Email webhook error"):
            message_service.process_inbound_email_webhook(webhook_data)