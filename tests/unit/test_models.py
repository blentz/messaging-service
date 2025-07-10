"""
Unit tests for database models.
"""

from app.models.conversation import Conversation, ConversationType
from app.models.message import (
    Message,
    MessageDirection,
    MessageStatus,
    MessageType,
    ProviderName,
)
from app.models.provider import Provider, ProviderType
from app.utils.database import db


class TestConversationModel:
    """Test the Conversation model."""

    def test_conversation_creation(self, app):
        """Test creating a conversation."""
        with app.app_context():
            conversation = Conversation(
                participants=["+18045551234", "+12016661234"],
                conversation_type=ConversationType.SMS_MMS,
            )
            db.session.add(conversation)
            db.session.commit()

            assert conversation.id is not None
            assert conversation.participants == ["+18045551234", "+12016661234"]
            assert conversation.conversation_type == ConversationType.SMS_MMS
            assert conversation.message_count == 0
            assert conversation.created_at is not None
            assert conversation.updated_at is not None

    def test_find_by_participants(self, app):
        """Test finding conversation by participants."""
        with app.app_context():
            participants = ["+18045551234", "+12016661234"]
            conversation = Conversation(
                participants=participants, conversation_type=ConversationType.SMS_MMS
            )
            db.session.add(conversation)
            db.session.commit()

            found = Conversation.find_by_participants(participants)
            assert found is not None
            assert found.id == conversation.id
            assert found.participants == participants

    def test_add_message(self, app):
        """Test adding a message to conversation."""
        with app.app_context():
            conversation = Conversation(
                participants=["+18045551234", "+12016661234"],
                conversation_type=ConversationType.SMS_MMS,
            )
            db.session.add(conversation)
            db.session.commit()

            initial_count = conversation.message_count
            initial_updated = conversation.updated_at

            conversation.add_message()

            assert conversation.message_count == initial_count + 1
            assert conversation.last_message_at is not None
            assert conversation.updated_at > initial_updated

    def test_to_dict(self, app):
        """Test conversation to_dict method."""
        with app.app_context():
            conversation = Conversation(
                participants=["+18045551234", "+12016661234"],
                conversation_type=ConversationType.EMAIL,
                extra_data={"test": "data"},
            )
            db.session.add(conversation)
            db.session.commit()

            data = conversation.to_dict()

            assert data["id"] == conversation.id
            assert data["participants"] == ["+18045551234", "+12016661234"]
            assert data["conversation_type"] == "email"
            assert data["message_count"] == 0
            assert data["metadata"] == {"test": "data"}
            assert "created_at" in data
            assert "updated_at" in data


class TestMessageModel:
    """Test the Message model."""

    def test_message_creation(self, app):
        """Test creating a message."""
        with app.app_context():
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
                attachments=[],
                status=MessageStatus.PENDING,
            )
            db.session.add(message)
            db.session.commit()

            assert message.id is not None
            assert message.conversation_id == conversation.id
            assert message.from_address == "+18045551234"
            assert message.to_address == "+12016661234"
            assert message.message_type == MessageType.SMS
            assert message.direction == MessageDirection.OUTBOUND
            assert message.body == "Test message"
            assert message.status == MessageStatus.PENDING

    def test_mark_sent(self, app):
        """Test marking message as sent."""
        with app.app_context():
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

            message.mark_sent("test_provider_id", ProviderName.TWILIO_MOCK)

            assert message.status == MessageStatus.SENT
            assert message.provider_id == "test_provider_id"
            assert message.provider_name == ProviderName.TWILIO_MOCK
            assert message.sent_at is not None

    def test_mark_failed(self, app):
        """Test marking message as failed."""
        with app.app_context():
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

            original_updated = message.updated_at
            message.mark_failed()

            assert message.status == MessageStatus.FAILED
            assert message.updated_at > original_updated

    def test_to_dict(self, app):
        """Test message to_dict method."""
        with app.app_context():
            conversation = Conversation(
                participants=["+18045551234", "+12016661234"],
                conversation_type=ConversationType.EMAIL,
            )
            db.session.add(conversation)
            db.session.commit()

            message = Message(
                conversation_id=conversation.id,
                from_address="test@example.com",
                to_address="user@example.com",
                message_type=MessageType.EMAIL,
                direction=MessageDirection.INBOUND,
                body="Test email message",
                attachments=["http://example.com/file.pdf"],
                provider_id="email_123",
                provider_name=ProviderName.SENDGRID_MOCK,
                status=MessageStatus.DELIVERED,
            )
            db.session.add(message)
            db.session.commit()

            data = message.to_dict()

            assert data["id"] == message.id
            assert data["conversation_id"] == conversation.id
            assert data["from"] == "test@example.com"
            assert data["to"] == "user@example.com"
            assert data["type"] == "email"
            assert data["direction"] == "inbound"
            assert data["body"] == "Test email message"
            assert data["attachments"] == ["http://example.com/file.pdf"]
            assert data["provider_id"] == "email_123"
            assert data["provider_name"] == "sendgrid_mock"
            assert data["status"] == "delivered"


class TestProviderModel:
    """Test the Provider model."""

    def test_provider_creation(self, app):
        """Test creating a provider."""
        with app.app_context():
            provider = Provider(
                name="test_provider",
                provider_type=ProviderType.SMS_MMS,
                config={"api_key": "test_key"},
                is_active=True,
                error_simulation={"error_rate": 0.1},
            )
            db.session.add(provider)
            db.session.commit()

            assert provider.id is not None
            assert provider.name == "test_provider"
            assert provider.provider_type == ProviderType.SMS_MMS
            assert provider.config == {"api_key": "test_key"}
            assert provider.is_active is True
            assert provider.error_simulation == {"error_rate": 0.1}

    def test_get_by_name(self, app):
        """Test getting provider by name."""
        with app.app_context():
            provider = Provider(
                name="unique_provider", provider_type=ProviderType.EMAIL, is_active=True
            )
            db.session.add(provider)
            db.session.commit()

            found = Provider.get_by_name("unique_provider")
            assert found is not None
            assert found.id == provider.id
            assert found.name == "unique_provider"

            not_found = Provider.get_by_name("nonexistent")
            assert not_found is None

    def test_get_active_providers(self, app):
        """Test getting active providers."""
        with app.app_context():
            active_sms = Provider(
                name="active_sms", provider_type=ProviderType.SMS_MMS, is_active=True
            )
            inactive_sms = Provider(
                name="inactive_sms", provider_type=ProviderType.SMS_MMS, is_active=False
            )
            active_email = Provider(
                name="active_email", provider_type=ProviderType.EMAIL, is_active=True
            )

            db.session.add_all([active_sms, inactive_sms, active_email])
            db.session.commit()

            # Test getting all active providers
            all_active = Provider.get_active_providers()
            assert len(all_active) == 2
            assert active_sms in all_active
            assert active_email in all_active
            assert inactive_sms not in all_active

            # Test filtering by provider type
            sms_active = Provider.get_active_providers(ProviderType.SMS_MMS)
            assert len(sms_active) == 1
            assert sms_active[0] == active_sms

    def test_to_dict(self, app):
        """Test provider to_dict method."""
        with app.app_context():
            provider = Provider(
                name="test_provider",
                provider_type=ProviderType.EMAIL,
                config={"endpoint": "https://api.test.com"},
                is_active=False,
                error_simulation={"timeout_rate": 0.05},
            )
            db.session.add(provider)
            db.session.commit()

            data = provider.to_dict()

            assert data["id"] == provider.id
            assert data["name"] == "test_provider"
            assert data["provider_type"] == "email"
            assert data["config"] == {"endpoint": "https://api.test.com"}
            assert data["is_active"] is False
            assert data["error_simulation"] == {"timeout_rate": 0.05}
