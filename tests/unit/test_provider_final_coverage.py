"""
Final tests to achieve 100% provider coverage.
"""

import pytest
from unittest.mock import patch

from app.providers.base import MockProviderBase
from app.providers.twilio_mock import TwilioMockProvider
from app.providers.sendgrid_mock import SendGridMockProvider
from app.providers.base import ProviderError


class TestProviderFinalCoverage:
    """Final tests for missing provider coverage."""

    def test_base_provider_health_check_direct(self):
        """Test base provider health_check method directly."""
        provider = TwilioMockProvider()
        
        # Call the parent method directly to hit line 41 in base.py
        with patch('time.time', return_value=2000.0):
            health = super(TwilioMockProvider, provider).health_check()
        
        expected = {
            "status": "healthy",
            "provider": "twilio_mock",
            "timestamp": 2000.0
        }
        assert health == expected

    def test_twilio_invalid_message_type(self):
        """Test Twilio validation with invalid message type."""
        provider = TwilioMockProvider()
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "body": "Test message",
            "type": "invalid_type"
        }
        
        with pytest.raises(ProviderError, match="Invalid message type: invalid_type"):
            provider.validate_request(message_data)

    def test_twilio_mms_too_many_attachments(self):
        """Test Twilio validation with too many MMS attachments."""
        provider = TwilioMockProvider()
        
        message_data = {
            "from": "+12016661234", 
            "to": "+18045551234",
            "body": "MMS with too many attachments",
            "type": "mms",
            "attachments": ["url"] * 11  # Over 10 attachment limit
        }
        
        with pytest.raises(ProviderError, match="MMS messages cannot have more than 10 attachments"):
            provider.validate_request(message_data)

    def test_twilio_health_check_override(self):
        """Test Twilio health_check override method."""
        provider = TwilioMockProvider()
        
        with patch('time.time', return_value=3000.0):
            health = provider.health_check()
        
        assert health["status"] == "healthy"
        assert health["provider"] == "twilio_mock" 
        assert health["timestamp"] == 3000.0
        assert health["account_sid"] == "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        assert health["api_version"] == "2010-04-01"

    def test_sendgrid_empty_body_validation(self):
        """Test SendGrid validation with empty body."""
        provider = SendGridMockProvider()
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com", 
            "body": ""  # Empty body
        }
        
        with pytest.raises(ProviderError, match="Message body cannot be empty"):
            provider.validate_request(message_data)

    def test_sendgrid_too_many_attachments(self):
        """Test SendGrid validation with too many attachments."""
        provider = SendGridMockProvider()
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": "Email with too many attachments",
            "attachments": ["attachment"] * 26  # Over 25 attachment limit
        }
        
        with pytest.raises(ProviderError, match="Email cannot have more than 25 attachments"):
            provider.validate_request(message_data)

    def test_sendgrid_health_check_override(self):
        """Test SendGrid health_check override method."""
        provider = SendGridMockProvider()
        
        with patch('time.time', return_value=4000.0):
            health = provider.health_check()
        
        assert health["status"] == "healthy"
        assert health["provider"] == "sendgrid_mock"
        assert health["timestamp"] == 4000.0
        assert health["api_version"] == "v3"

    def test_sendgrid_extract_subject_html(self):
        """Test SendGrid subject extraction from HTML body."""
        provider = SendGridMockProvider()
        
        html_body = "<html><head><title>Test Subject</title></head><body>Content</body></html>"
        
        # Call the private method
        subject = provider._extract_subject_from_body(html_body)
        assert subject == "Test Subject"

    def test_sendgrid_extract_subject_html_no_title(self):
        """Test SendGrid subject extraction from HTML without title."""
        provider = SendGridMockProvider()
        
        html_body = "<html><body>First line content\nSecond line</body></html>"
        
        # Call the private method  
        subject = provider._extract_subject_from_body(html_body)
        assert subject == "<html><body>First line content"  # First 50 chars

    def test_sendgrid_extract_subject_plain_text(self):
        """Test SendGrid subject extraction from plain text."""
        provider = SendGridMockProvider()
        
        plain_body = "This is the first line of content\nSecond line here"
        
        # Call the private method
        subject = provider._extract_subject_from_body(plain_body)
        assert subject == "This is the first line of content"

    def test_sendgrid_extract_subject_empty_body(self):
        """Test SendGrid subject extraction from empty body."""
        provider = SendGridMockProvider()
        
        empty_body = ""
        
        # Call the private method
        subject = provider._extract_subject_from_body(empty_body)
        assert subject == "Message from messaging service"