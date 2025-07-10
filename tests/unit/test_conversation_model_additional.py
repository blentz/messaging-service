"""
Additional unit tests for Conversation model to achieve 100% coverage.
"""

import json
import pytest
from app.models.conversation import Conversation, ConversationType
from app.utils.database import db


class TestConversationModelAdditional:
    """Additional tests for missing Conversation model coverage."""

    def test_conversation_repr(self, app):
        """Test conversation __repr__ method."""
        with app.app_context():
            conversation = Conversation(
                participants=["+18045551234", "+12016661234"],
                conversation_type=ConversationType.SMS_MMS,
            )
            db.session.add(conversation)
            db.session.commit()

            # Test the __repr__ method
            repr_str = repr(conversation)
            expected = f"<Conversation {conversation.id}: ['+18045551234', '+12016661234']>"
            assert repr_str == expected

    def test_find_by_participants_with_string_json(self, app):
        """Test find_by_participants when participants stored as JSON string."""
        with app.app_context():
            # Create a conversation with participants as a JSON string
            participants = ["+18045551234", "+12016661234"]
            conversation = Conversation(
                participants=participants,
                conversation_type=ConversationType.SMS_MMS,
            )
            db.session.add(conversation)
            db.session.commit()
            
            # Manually modify the participants to be a JSON string to test the parsing path
            # This simulates a database that stores JSON as strings
            conversation.participants = json.dumps(participants)
            db.session.commit()
            
            # Test finding with the JSON string parsing path
            found = Conversation.find_by_participants(participants)
            assert found is not None
            assert found.id == conversation.id

    def test_find_by_participants_not_found(self, app):
        """Test find_by_participants when no matching conversation exists."""
        with app.app_context():
            # Create a conversation with different participants
            conversation = Conversation(
                participants=["+18045551234", "+12016661234"],
                conversation_type=ConversationType.SMS_MMS,
            )
            db.session.add(conversation)
            db.session.commit()

            # Try to find with different participants
            found = Conversation.find_by_participants(["+19995551234", "+14445551234"])
            assert found is None

    def test_find_by_participants_empty_database(self, app):
        """Test find_by_participants when database is empty."""
        with app.app_context():
            # Don't create any conversations
            found = Conversation.find_by_participants(["+18045551234", "+12016661234"])
            assert found is None