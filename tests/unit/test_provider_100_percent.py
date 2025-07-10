"""
Final tests to achieve 100% provider coverage for the last 3 lines.
"""

from app.providers.sendgrid_mock import SendGridMockProvider
from app.providers.twilio_mock import TwilioMockProvider


class TestProvider100Percent:
    """Tests for the final 3 missing lines."""

    def test_sendgrid_detect_content_type_html(self):
        """Test SendGrid content type detection for HTML (line 148)."""
        provider = SendGridMockProvider()
        
        html_body = "<html><body>HTML content</body></html>"
        content_type = provider._detect_content_type(html_body)
        
        assert content_type == "text/html"

    def test_sendgrid_generate_webhook_payload(self):
        """Test SendGrid webhook payload generation (line 161)."""
        provider = SendGridMockProvider()
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": "Webhook test message"
        }
        
        payload = provider.generate_webhook_payload(message_data)
        
        assert payload["email"] == "recipient@example.com"
        assert "timestamp" in payload
        assert "smtp-id" in payload

    def test_twilio_generate_webhook_payload(self):
        """Test Twilio webhook payload generation (line 169)."""
        provider = TwilioMockProvider()
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234", 
            "body": "Webhook test message"
        }
        
        payload = provider.generate_webhook_payload(message_data)
        
        assert "MessageSid" in payload
        assert payload["From"] == "+12016661234"
        assert payload["To"] == "+18045551234"