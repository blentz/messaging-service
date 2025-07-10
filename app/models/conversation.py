"""
Conversation model for grouping messages by participants.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Integer, func
from sqlalchemy.dialects.postgresql import ENUM, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.utils.database import db


class ConversationType(Enum):
    """Enum for conversation types."""

    SMS_MMS = "sms_mms"
    EMAIL = "email"
    MIXED = "mixed"


class Conversation(db.Model):
    """
    Conversation model for grouping messages by participants.

    Groups messages between the same set of participants (phone numbers/emails).
    Supports mixed message types (SMS/MMS/Email) in the same conversation.
    """

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    participants: Mapped[dict] = mapped_column(JSON, nullable=False)
    conversation_type: Mapped[ConversationType] = mapped_column(
        ENUM(ConversationType), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    last_message_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="conversation", lazy="dynamic")

    def __repr__(self):
        return f"<Conversation {self.id}: {self.participants}>"

    @classmethod
    def find_by_participants(cls, participants):
        """Find conversation by participant list."""
        # Database-agnostic approach: get all conversations and filter in Python
        sorted_participants = sorted(participants)
        all_conversations = cls.query.all()
        
        for conversation in all_conversations:
            # Handle both list and string formats of participants
            conv_participants = conversation.participants
            if isinstance(conv_participants, str):
                import json
                conv_participants = json.loads(conv_participants)
            
            if sorted(conv_participants) == sorted_participants:
                return conversation
                
        return None

    def add_message(self):
        """Update conversation metadata when a message is added."""
        self.message_count += 1
        self.last_message_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """Convert conversation to dictionary for API responses."""
        return {
            "id": self.id,
            "participants": self.participants,
            "conversation_type": self.conversation_type.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_message_at": self.last_message_at.isoformat()
            if self.last_message_at
            else None,
            "message_count": self.message_count,
            "metadata": self.extra_data,
        }
