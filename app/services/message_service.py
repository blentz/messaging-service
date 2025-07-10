"""
Business logic for message processing and routing.
"""

import time
from datetime import datetime

from app.models.message import (
    Message,
    MessageDirection,
    MessageStatus,
    MessageType,
    ProviderName,
)
from app.providers.base import ProviderError
from app.services.conversation_service import ConversationService
from app.services.provider_service import ProviderService
from app.utils.database import db
from app.utils.logging import get_logger, log_message_event
from app.utils.metrics import get_metrics_manager


class MessageService:
    """Service for processing and routing messages."""

    def __init__(self):
        self.logger = get_logger()
        self.metrics = get_metrics_manager()
        self.conversation_service = ConversationService()
        self.provider_service = ProviderService()

    def send_sms_message(
        self,
        from_address: str,
        to_address: str,
        message_type: str,
        body: str,
        attachments: list[str] | None = None,
        timestamp: str | None = None,
    ) -> dict:
        """
        Send SMS/MMS message through provider.

        Args:
            from_address: Sender phone number
            to_address: Recipient phone number
            message_type: 'sms' or 'mms'
            body: Message content
            attachments: Optional list of attachment URLs
            timestamp: Optional ISO timestamp

        Returns:
            Dict with message_id, status, conversation_id, sent_at
        """
        start_time = time.time()

        try:
            # Validate message type
            msg_type = (
                MessageType.SMS if message_type.lower() == "sms" else MessageType.MMS
            )

            # Find or create conversation
            conversation = self.conversation_service.find_or_create_conversation(
                from_address, to_address, msg_type
            )

            # Create message record
            message = Message(
                from_address=from_address,
                to_address=to_address,
                message_type=msg_type,
                direction=MessageDirection.OUTBOUND,
                body=body,
                attachments=attachments or [],
                status=MessageStatus.PENDING,
            )

            # Add to conversation
            self.conversation_service.add_message_to_conversation(conversation, message)

            # Send through provider
            provider_response = self.provider_service.send_sms_message(
                {
                    "from": from_address,
                    "to": to_address,
                    "type": message_type,
                    "body": body,
                    "attachments": attachments or [],
                    "timestamp": timestamp or datetime.utcnow().isoformat(),
                }
            )

            # Update message with provider response
            message.mark_sent(
                provider_id=provider_response.get("sid"),
                provider_name=ProviderName.TWILIO_MOCK,
            )
            db.session.commit()

            # Log and metrics
            duration = time.time() - start_time
            log_message_event(
                "sms_message_sent",
                message_id=message.id,
                conversation_id=conversation.id,
                message_type=message_type,
                provider_id=provider_response.get("sid"),
            )
            self.metrics.increment_counter(
                "messages_sent_total", message_type=message_type
            )
            self.metrics.record_histogram(
                "message_processing_duration_seconds",
                duration,
                message_type=message_type,
            )

            return {
                "message_id": message.id,
                "status": message.status.value,
                "conversation_id": conversation.id,
                "sent_at": message.sent_at.isoformat(),
            }

        except ProviderError:
            # Re-raise ProviderError to maintain proper status codes
            raise
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                "Failed to send SMS message",
                error=str(e),
                from_address=from_address,
                to_address=to_address,
            )
            self.metrics.record_histogram(
                "message_processing_duration_seconds",
                duration,
                message_type=message_type,
                status="error",
            )
            raise

    def send_email_message(
        self,
        from_address: str,
        to_address: str,
        body: str,
        attachments: list[str] | None = None,
        timestamp: str | None = None,
    ) -> dict:
        """
        Send email message through provider.

        Args:
            from_address: Sender email address
            to_address: Recipient email address
            body: Message content (plain text or HTML)
            attachments: Optional list of attachment URLs
            timestamp: Optional ISO timestamp

        Returns:
            Dict with message_id, status, conversation_id, sent_at
        """
        start_time = time.time()

        try:
            # Find or create conversation
            conversation = self.conversation_service.find_or_create_conversation(
                from_address, to_address, MessageType.EMAIL
            )

            # Create message record
            message = Message(
                from_address=from_address,
                to_address=to_address,
                message_type=MessageType.EMAIL,
                direction=MessageDirection.OUTBOUND,
                body=body,
                attachments=attachments or [],
                status=MessageStatus.PENDING,
            )

            # Add to conversation
            self.conversation_service.add_message_to_conversation(conversation, message)

            # Send through provider
            provider_response = self.provider_service.send_email_message(
                {
                    "from": from_address,
                    "to": to_address,
                    "body": body,
                    "attachments": attachments or [],
                    "timestamp": timestamp or datetime.utcnow().isoformat(),
                }
            )

            # Update message with provider response
            message.mark_sent(
                provider_id=provider_response.get("message_id"),
                provider_name=ProviderName.SENDGRID_MOCK,
            )
            db.session.commit()

            # Log and metrics
            duration = time.time() - start_time
            log_message_event(
                "email_message_sent",
                message_id=message.id,
                conversation_id=conversation.id,
                provider_id=provider_response.get("message_id"),
            )
            self.metrics.increment_counter("messages_sent_total", message_type="email")
            self.metrics.record_histogram(
                "message_processing_duration_seconds", duration, message_type="email"
            )

            return {
                "message_id": message.id,
                "status": message.status.value,
                "conversation_id": conversation.id,
                "sent_at": message.sent_at.isoformat(),
            }

        except ProviderError:
            # Re-raise ProviderError to maintain proper status codes
            raise
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                "Failed to send email message",
                error=str(e),
                from_address=from_address,
                to_address=to_address,
            )
            self.metrics.record_histogram(
                "message_processing_duration_seconds",
                duration,
                message_type="email",
                status="error",
            )
            raise

    def process_inbound_sms_webhook(self, webhook_data: dict) -> dict:
        """
        Process inbound SMS/MMS webhook from provider.

        Args:
            webhook_data: Webhook payload data

        Returns:
            Dict with processing status
        """
        start_time = time.time()

        try:
            # Extract data from webhook
            from_address = webhook_data["from"]
            to_address = webhook_data["to"]
            message_type = (
                MessageType.SMS if webhook_data["type"] == "sms" else MessageType.MMS
            )
            provider_id = webhook_data["messaging_provider_id"]
            body = webhook_data["body"]
            attachments = webhook_data.get("attachments", [])

            # Find or create conversation
            conversation = self.conversation_service.find_or_create_conversation(
                from_address, to_address, message_type
            )

            # Create inbound message
            message = Message(
                from_address=from_address,
                to_address=to_address,
                message_type=message_type,
                direction=MessageDirection.INBOUND,
                body=body,
                attachments=attachments,
                provider_id=provider_id,
                provider_name=ProviderName.TWILIO_MOCK,
                status=MessageStatus.DELIVERED,
            )

            # Add to conversation
            self.conversation_service.add_message_to_conversation(conversation, message)

            # Log and metrics
            duration = time.time() - start_time
            log_message_event(
                "inbound_sms_processed",
                message_id=message.id,
                conversation_id=conversation.id,
                provider_id=provider_id,
                message_type=message_type.value,
            )
            self.metrics.increment_counter(
                "messages_received_total", message_type=message_type.value
            )
            self.metrics.record_histogram(
                "webhook_processing_duration_seconds",
                duration,
                message_type=message_type.value,
            )

            return {"status": "processed", "message_id": message.id}

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                "Failed to process inbound SMS webhook",
                error=str(e),
                webhook_data=webhook_data,
            )
            self.metrics.record_histogram(
                "webhook_processing_duration_seconds",
                duration,
                message_type="sms",
                status="error",
            )
            raise

    def process_inbound_email_webhook(self, webhook_data: dict) -> dict:
        """
        Process inbound email webhook from provider.

        Args:
            webhook_data: Webhook payload data

        Returns:
            Dict with processing status
        """
        start_time = time.time()

        try:
            # Extract data from webhook
            from_address = webhook_data["from"]
            to_address = webhook_data["to"]
            provider_id = webhook_data["xillio_id"]
            body = webhook_data["body"]
            attachments = webhook_data.get("attachments", [])

            # Find or create conversation
            conversation = self.conversation_service.find_or_create_conversation(
                from_address, to_address, MessageType.EMAIL
            )

            # Create inbound message
            message = Message(
                from_address=from_address,
                to_address=to_address,
                message_type=MessageType.EMAIL,
                direction=MessageDirection.INBOUND,
                body=body,
                attachments=attachments,
                provider_id=provider_id,
                provider_name=ProviderName.SENDGRID_MOCK,
                status=MessageStatus.DELIVERED,
            )

            # Add to conversation
            self.conversation_service.add_message_to_conversation(conversation, message)

            # Log and metrics
            duration = time.time() - start_time
            log_message_event(
                "inbound_email_processed",
                message_id=message.id,
                conversation_id=conversation.id,
                provider_id=provider_id,
            )
            self.metrics.increment_counter(
                "messages_received_total", message_type="email"
            )
            self.metrics.record_histogram(
                "webhook_processing_duration_seconds", duration, message_type="email"
            )

            return {"status": "processed", "message_id": message.id}

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                "Failed to process inbound email webhook",
                error=str(e),
                webhook_data=webhook_data,
            )
            self.metrics.record_histogram(
                "webhook_processing_duration_seconds",
                duration,
                message_type="email",
                status="error",
            )
            raise
