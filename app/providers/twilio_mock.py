"""
Mock Twilio provider implementation using OpenAPI specification.
"""

import re
import time
from datetime import datetime

from app.providers.base import MockProviderBase, ProviderError


class TwilioMockProvider(MockProviderBase):
    """
    Mock Twilio provider implementation.

    Based on Twilio OpenAPI specification for SMS/MMS messaging.
    Simulates Twilio's Messages API endpoints and response formats.
    """

    def __init__(self):
        super().__init__("twilio_mock")
        self.account_sid = "AC" + "x" * 32  # Mock Account SID
        self.api_version = "2010-04-01"

    def send_message(self, message_data: dict) -> dict:
        """
        Send SMS/MMS message through Twilio mock.

        Implements Twilio's POST /2010-04-01/Accounts/{AccountSid}/Messages.json

        Args:
            message_data: Message data with keys: from, to, type, body, attachments

        Returns:
            Dict matching Twilio API response format
        """
        # Validate request
        self.validate_request(message_data)

        # Simulate provider errors
        self.simulate_errors()

        # Generate mock response matching Twilio format
        message_sid = self.generate_message_sid()
        response = {
            "sid": message_sid,
            "account_sid": self.account_sid,
            "from": message_data["from"],
            "to": message_data["to"],
            "body": message_data["body"],
            "status": "sent",
            "direction": "outbound-api",
            "api_version": self.api_version,
            "price": "0.0075",
            "price_unit": "USD",
            "uri": f"/2010-04-01/Accounts/{self.account_sid}/Messages/{message_sid}.json",
            "date_created": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "date_updated": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "date_sent": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "error_code": None,
            "error_message": None,
            "messaging_service_sid": None,
            "num_segments": "1",
            "num_media": str(len(message_data.get("attachments", []))),
            "subresource_uris": {
                "media": f"/2010-04-01/Accounts/{self.account_sid}/Messages/{message_sid}/Media.json"
            },
        }

        # Add MMS-specific fields if attachments present
        if message_data.get("attachments"):
            response["media_url"] = message_data["attachments"]

        self.logger.info(
            "Twilio mock message sent",
            message_sid=message_sid,
            from_number=message_data["from"],
            to_number=message_data["to"],
            message_type=message_data.get("type", "sms"),
        )

        return response

    def validate_request(self, message_data: dict) -> bool:
        """
        Validate request against Twilio API requirements.

        Args:
            message_data: Message data to validate

        Returns:
            True if valid

        Raises:
            ProviderError: If validation fails
        """
        required_fields = ["from", "to", "body"]
        for field in required_fields:
            if field not in message_data:
                missing_field_msg = f"Missing required field: {field}"
                raise ProviderError(missing_field_msg, status_code=400)

        # Validate phone number formats (E.164)
        phone_pattern = r"^\+[1-9]\d{1,14}$"

        if not re.match(phone_pattern, message_data["from"]):
            invalid_from_msg = (
                f"Invalid 'from' phone number format: {message_data['from']}"
            )
            raise ProviderError(invalid_from_msg, status_code=400)

        if not re.match(phone_pattern, message_data["to"]):
            invalid_to_msg = f"Invalid 'to' phone number format: {message_data['to']}"
            raise ProviderError(invalid_to_msg, status_code=400)

        # Validate message body
        if not message_data["body"] or len(message_data["body"]) > 1600:
            body_length_msg = "Message body must be between 1 and 1600 characters"
            raise ProviderError(body_length_msg, status_code=400)

        # Validate message type
        message_type = message_data.get("type", "sms").lower()
        if message_type not in ["sms", "mms"]:
            invalid_type_msg = (
                f"Invalid message type: {message_type}. Must be 'sms' or 'mms'"
            )
            raise ProviderError(invalid_type_msg, status_code=400)

        # Validate MMS attachments
        if message_type == "mms":
            attachments = message_data.get("attachments", [])
            if attachments and len(attachments) > 10:
                mms_attachments_msg = (
                    "MMS messages cannot have more than 10 attachments"
                )
                raise ProviderError(mms_attachments_msg, status_code=400)

        return True

    def generate_message_sid(self) -> str:
        """Generate a Twilio-formatted message SID."""
        return "SM" + self.generate_mock_id()

    def health_check(self) -> dict:
        """
        Check Twilio provider health status.
        
        Returns:
            Dict with health status information
        """
        return {
            "status": "healthy",
            "provider": self.provider_name,
            "account_sid": self.account_sid,
            "api_version": self.api_version,
            "timestamp": time.time()
        }

    def generate_webhook_payload(self, message_data: dict) -> dict:
        """
        Generate webhook payload for inbound messages.

        Args:
            message_data: Inbound message data

        Returns:
            Dict matching Twilio webhook format
        """
        return {
            "MessageSid": self.generate_message_sid(),
            "AccountSid": self.account_sid,
            "MessagingServiceSid": None,
            "From": message_data["from"],
            "To": message_data["to"],
            "Body": message_data["body"],
            "NumMedia": str(len(message_data.get("attachments", []))),
            "MediaUrl0": message_data.get("attachments", [None])[0],
            "MediaContentType0": "image/jpeg"
            if message_data.get("attachments")
            else None,
            "SmsStatus": "received",
            "ApiVersion": self.api_version,
            "SmsSid": self.generate_message_sid(),
        }
