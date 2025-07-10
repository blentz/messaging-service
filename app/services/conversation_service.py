"""
Business logic for conversation management.
"""

from sqlalchemy import desc, func

from app.models.conversation import Conversation, ConversationType
from app.models.message import Message, MessageType
from app.utils.database import db
from app.utils.logging import get_logger, log_message_event
from app.utils.metrics import get_metrics_manager


class ConversationService:
    """Service for managing conversations and grouping messages."""

    def __init__(self):
        self.logger = get_logger()
        self.metrics = get_metrics_manager()

    def find_or_create_conversation(
        self, from_address: str, to_address: str, message_type: MessageType
    ) -> Conversation:
        """
        Find existing conversation or create new one for participants.

        Groups messages by individual data points (from/to addresses).
        Supports mixed message types in the same conversation.
        """
        # Normalize participants (sort to ensure consistent matching)
        participants = sorted([from_address, to_address])

        # Try to find existing conversation
        conversation = Conversation.find_by_participants(participants)

        if conversation:
            # Update conversation type if needed (mixed type support)
            self._update_conversation_type(conversation, message_type)
            return conversation

        # Create new conversation
        conversation_type = self._determine_conversation_type(message_type)
        conversation = Conversation(
            participants=participants, conversation_type=conversation_type
        )

        db.session.add(conversation)
        db.session.commit()

        # Log and track metrics
        log_message_event(
            "conversation_created",
            conversation_id=conversation.id,
            participants=participants,
            conversation_type=conversation_type.value,
        )
        self.metrics.increment_counter(
            "conversation_creation_total", conversation_type=conversation_type.value
        )

        return conversation

    def get_conversations(
        self, limit: int = 50, offset: int = 0, search: str | None = None
    ) -> tuple[list[Conversation], int]:
        """
        Get conversations list with pagination and optional search.

        Args:
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            search: Optional search term for participant filtering

        Returns:
            Tuple of (conversations list, total count)
        """
        query = Conversation.query

        # Apply search filter if provided
        if search:
            query = query.filter(
                func.cast(Conversation.participants, db.Text).contains(search)
            )

        # Get total count for pagination
        total = query.count()

        # Apply pagination and ordering
        conversations = (
            query.order_by(
                desc(Conversation.last_message_at), desc(Conversation.created_at)
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        return conversations, total

    def get_conversation_messages(
        self,
        conversation_id: int,
        limit: int = 50,
        offset: int = 0,
        since: str | None = None,
    ) -> tuple[list[Message], int]:
        """
        Get messages for a specific conversation.

        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            since: ISO timestamp to filter messages after

        Returns:
            Tuple of (messages list, total count)
        """
        query = Message.query.filter_by(conversation_id=conversation_id)

        # Apply since filter if provided
        if since:
            try:
                from datetime import datetime

                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                query = query.filter(Message.created_at >= since_dt)
            except ValueError:
                self.logger.warning("Invalid since timestamp format", since=since)

        # Get total count
        total = query.count()

        # Apply pagination and ordering (newest first)
        messages = (
            query.order_by(desc(Message.created_at)).offset(offset).limit(limit).all()
        )

        return messages, total

    def add_message_to_conversation(
        self, conversation: Conversation, message: Message
    ) -> None:
        """
        Add a message to a conversation and update metadata.

        Args:
            conversation: Conversation to update
            message: Message to add
        """
        message.conversation_id = conversation.id
        conversation.add_message()

        # Update conversation type if needed for mixed conversations
        self._update_conversation_type(conversation, message.message_type)

        # Add message to database session before committing
        db.session.add(message)
        db.session.commit()

        log_message_event(
            "message_added_to_conversation",
            conversation_id=conversation.id,
            message_id=message.id,
            message_type=message.message_type.value,
        )

    def _determine_conversation_type(
        self, message_type: MessageType
    ) -> ConversationType:
        """Determine conversation type based on first message type."""
        if message_type in [MessageType.SMS, MessageType.MMS]:
            return ConversationType.SMS_MMS
        if message_type == MessageType.EMAIL:
            return ConversationType.EMAIL
        return ConversationType.MIXED

    def _update_conversation_type(
        self, conversation: Conversation, message_type: MessageType
    ) -> None:
        """Update conversation type to mixed if different message types are used."""
        current_type = conversation.conversation_type
        new_type = self._determine_conversation_type(message_type)

        # If types are different, mark as mixed
        if current_type != new_type and current_type != ConversationType.MIXED:
            conversation.conversation_type = ConversationType.MIXED

            log_message_event(
                "conversation_type_updated_to_mixed",
                conversation_id=conversation.id,
                previous_type=current_type.value,
                new_message_type=message_type.value,
            )
