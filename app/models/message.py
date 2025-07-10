"""
Message model for storing SMS/MMS and Email messages.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.utils.database import db


class MessageType(Enum):
    """Enum for message types."""

    SMS = "sms"
    MMS = "mms"
    EMAIL = "email"


class MessageDirection(Enum):
    """Enum for message direction."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(Enum):
    """Enum for message status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class ProviderName(Enum):
    """Enum for provider names."""

    TWILIO_MOCK = "twilio_mock"
    SENDGRID_MOCK = "sendgrid_mock"


class Message(db.Model):
    """
    Message model for storing all message content and metadata.

    Supports SMS, MMS, and Email messages with provider-specific IDs,
    attachments, and comprehensive status tracking.
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=False
    )
    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
    to_address: Mapped[str] = mapped_column(String(255), nullable=False)
    message_type: Mapped[MessageType] = mapped_column(ENUM(MessageType), nullable=False)
    direction: Mapped[MessageDirection] = mapped_column(
        ENUM(MessageDirection), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[list] = mapped_column(JSON, nullable=True)
    provider_id: Mapped[str] = mapped_column(String(255), nullable=True)
    provider_name: Mapped[ProviderName] = mapped_column(
        ENUM(ProviderName), nullable=True
    )
    status: Mapped[MessageStatus] = mapped_column(
        ENUM(MessageStatus), nullable=False, default=MessageStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    sent_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return (
            f"<Message {self.id}: {self.message_type.value} from {self.from_address}>"
        )

    def to_dict(self):
        """Convert message to dictionary for API responses."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "from": self.from_address,
            "to": self.to_address,
            "type": self.message_type.value,
            "direction": self.direction.value,
            "body": self.body,
            "attachments": self.attachments or [],
            "provider_id": self.provider_id,
            "provider_name": self.provider_name.value if self.provider_name else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }

    def mark_sent(self, provider_id=None, provider_name=None):
        """Mark message as sent with provider information."""
        self.status = MessageStatus.SENT
        self.sent_at = datetime.utcnow()
        if provider_id:
            self.provider_id = provider_id
        if provider_name:
            self.provider_name = provider_name

    def mark_failed(self):
        """Mark message as failed."""
        self.status = MessageStatus.FAILED
        self.updated_at = datetime.utcnow()
