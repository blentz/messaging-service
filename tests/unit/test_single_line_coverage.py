"""
Tests to cover single missing lines across different modules.
"""

import pytest
from unittest.mock import patch, Mock
from flask import Flask

from app.models.message import Message, MessageType, MessageDirection, MessageStatus
from app.models.provider import Provider, ProviderType
from app.models.conversation import Conversation, ConversationType
from app.services.conversation_service import ConversationService
from app.utils.logging import log_message_event
from app.utils.metrics import MetricsManager
from app.utils.database import db


class TestSingleLineCoverage:
    """Tests for single missing lines across modules."""

    def test_message_repr(self, app):
        """Test Message __repr__ method (line 87-88 in message.py)."""
        with app.app_context():
            # Create conversation first
            conversation = Conversation(
                participants=["+18045551234", "+12016661234"],
                conversation_type=ConversationType.SMS_MMS,
            )
            db.session.add(conversation)
            db.session.commit()

            message = Message(
                conversation_id=conversation.id,
                from_address="+18045551234",
                to_address="+12016661234",
                message_type=MessageType.SMS,
                direction=MessageDirection.OUTBOUND,
                body="Test message",
                status=MessageStatus.PENDING,
            )
            db.session.add(message)
            db.session.commit()

            # Test the __repr__ method  
            repr_str = repr(message)
            expected = f"<Message {message.id}: sms from +18045551234>"
            assert repr_str == expected

    def test_provider_repr(self, app):
        """Test Provider __repr__ method (line 41 in provider.py)."""
        with app.app_context():
            provider = Provider(
                name="test_provider",
                provider_type=ProviderType.SMS_MMS,
                config={"api_key": "test"},
                is_active=True,
            )
            db.session.add(provider)
            db.session.commit()

            # Test the __repr__ method
            repr_str = repr(provider)
            expected = f"<Provider test_provider: sms_mms>"
            assert repr_str == expected

    def test_conversation_service_determine_unknown_type(self):
        """Test conversation service _determine_conversation_type with unknown type (line 174)."""
        service = ConversationService()
        
        # Mock an unknown message type by creating a mock object
        mock_message_type = Mock()
        mock_message_type.name = "UNKNOWN"
        
        # This should hit the fallback return ConversationType.MIXED line
        result = service._determine_conversation_type(mock_message_type)
        assert result == ConversationType.MIXED

    @patch('app.utils.logging.get_logger')
    def test_log_message_event_with_message_id(self, mock_get_logger):
        """Test log_message_event with message_id (line 91 in logging.py)."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Call with message_id to trigger line 91
        log_message_event(
            "test_event",
            message_id="msg_123",
            conversation_id="conv_456",
            extra_field="extra_value"
        )
        
        # Verify logger was called with message_id in context
        mock_get_logger.assert_called_once_with(
            message_id="msg_123",
            conversation_id="conv_456",
            extra_field="extra_value"
        )
        mock_logger.info.assert_called_once_with("test_event")

    def test_metrics_manager_setup_disabled(self):
        """Test MetricsManager setup when metrics are disabled (line 24 in metrics.py)."""
        app = Flask(__name__)
        app.config['OTEL_METRICS_ENABLED'] = False
        
        manager = MetricsManager()
        
        # This should hit the early return on line 24
        result = manager.setup(app)
        assert result is None

    def test_validation_general_exception(self):
        """Test validation general exception handling (lines 309-310 in validation.py)."""
        from app.middleware.validation import _is_valid_iso_timestamp
        
        # Pass an invalid type to trigger a general exception
        with patch('builtins.__import__', side_effect=Exception("Mock import error")):
            result = _is_valid_iso_timestamp("2023-01-01T12:00:00Z")
            assert result is False