"""
Mock SendGrid provider implementation using OpenAPI specification.
"""

import re
import time
from datetime import datetime

from app.providers.base import MockProviderBase, ProviderError


class SendGridMockProvider(MockProviderBase):
    """
    Mock SendGrid provider implementation.

    Based on SendGrid OpenAPI v3.1 specification for email messaging.
    Simulates SendGrid's Mail Send API endpoints and response formats.
    """

    def __init__(self):
        super().__init__("sendgrid_mock")
        self.api_version = "v3"

    def send_message(self, message_data: dict) -> dict:
        """
        Send email message through SendGrid mock.

        Implements SendGrid's POST /v3/mail/send endpoint

        Args:
            message_data: Message data with keys: from, to, body, attachments

        Returns:
            Dict with message_id and status (SendGrid returns 202 Accepted)
        """
        # Validate request
        self.validate_request(message_data)

        # Simulate provider errors
        self.simulate_errors()

        # Generate mock response (SendGrid returns 202 Accepted with X-Message-Id header)
        message_id = self.generate_message_id()
        response = {
            "message_id": message_id,
            "status": "accepted",
            "status_code": 202,
            "timestamp": datetime.utcnow().isoformat(),
            "from": message_data["from"],
            "to": message_data["to"],
            "subject": self._extract_subject_from_body(message_data["body"]),
            "content_type": self._detect_content_type(message_data["body"]),
        }

        self.logger.info(
            "SendGrid mock email sent",
            message_id=message_id,
            from_email=message_data["from"],
            to_email=message_data["to"],
            content_type=response["content_type"],
        )

        return response

    def validate_request(self, message_data: dict) -> bool:
        """
        Validate request against SendGrid API requirements.

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

        # Validate email formats - more strict pattern
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, message_data["from"]):
            invalid_from_msg = f"Invalid 'from' email format: {message_data['from']}"
            raise ProviderError(invalid_from_msg, status_code=400)

        if not re.match(email_pattern, message_data["to"]):
            invalid_to_msg = f"Invalid 'to' email format: {message_data['to']}"
            raise ProviderError(invalid_to_msg, status_code=400)

        # Validate message body
        if not message_data["body"]:
            empty_body_msg = "Message body cannot be empty"
            raise ProviderError(empty_body_msg, status_code=400)

        # Validate body size (SendGrid limit is ~30MB, but we'll use 1MB for mock)
        if len(message_data["body"]) > 1024 * 1024:
            body_size_msg = "Message body exceeds maximum size limit"
            raise ProviderError(body_size_msg, status_code=400)

        # Validate attachments
        attachments = message_data.get("attachments", [])
        if attachments and len(attachments) > 25:
            attachments_limit_msg = "Email cannot have more than 25 attachments"
            raise ProviderError(attachments_limit_msg, status_code=400)

        return True

    def generate_message_id(self) -> str:
        """Generate a SendGrid-formatted message ID."""
        return f"sg_{self.generate_mock_id()}"

    def health_check(self) -> dict:
        """
        Check SendGrid provider health status.
        
        Returns:
            Dict with health status information
        """
        return {
            "status": "healthy",
            "provider": self.provider_name,
            "api_version": self.api_version,
            "timestamp": time.time()
        }

    def _extract_subject_from_body(self, body: str) -> str:
        """Extract subject from email body if HTML format, otherwise use default."""
        if body.startswith("<html>") or body.startswith("<!DOCTYPE"):
            # For HTML emails, try to extract title or use first line
            import re

            title_match = re.search(r"<title>(.*?)</title>", body, re.IGNORECASE)
            if title_match:
                return title_match.group(1)

        # For plain text, use first line up to 50 chars
        first_line = body.split("\n")[0][:50]
        return first_line if first_line else "Message from messaging service"

    def _detect_content_type(self, body: str) -> str:
        """Detect content type based on body content."""
        if body.strip().startswith(("<html>", "<!DOCTYPE")):
            return "text/html"
        return "text/plain"

    def generate_webhook_payload(self, message_data: dict) -> dict:
        """
        Generate webhook payload for inbound emails.

        Args:
            message_data: Inbound message data

        Returns:
            Dict matching SendGrid webhook format
        """
        return {
            "email": message_data["to"],
            "timestamp": int(datetime.utcnow().timestamp()),
            "smtp-id": f"<{self.generate_message_id()}@sendgrid.com>",
            "event": "delivered",
            "category": ["messaging-service"],
            "sg_event_id": self.generate_mock_id(),
            "sg_message_id": self.generate_message_id(),
            "response": "250 OK",
            "attempt": "1",
            "useragent": "Mozilla/5.0",
            "ip": "192.168.1.1",
            "url": None,
            "reason": None,
            "status": None,
            "from": message_data["from"],
            "subject": self._extract_subject_from_body(message_data["body"]),
            "html": message_data["body"]
            if self._detect_content_type(message_data["body"]) == "text/html"
            else None,
            "text": message_data["body"]
            if self._detect_content_type(message_data["body"]) == "text/plain"
            else None,
            "attachments": len(message_data.get("attachments", [])),
        }
