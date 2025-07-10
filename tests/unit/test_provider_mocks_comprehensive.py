"""
Comprehensive tests for provider mock classes to achieve 100% coverage.
"""

import pytest
import random
import time
from unittest.mock import patch, Mock

from app.providers.base import (
    MockProviderBase, ProviderError, ProviderRateLimitError, ProviderServerError
)
from app.providers.twilio_mock import TwilioMockProvider
from app.providers.sendgrid_mock import SendGridMockProvider


class TestMockProviderBase:
    """Comprehensive tests for MockProviderBase."""

    def test_health_check(self):
        """Test provider health_check method."""
        provider = TwilioMockProvider()  # Concrete implementation
        
        with patch('time.time', return_value=1000.0):
            health = provider.health_check()
            
        # TwilioMockProvider overrides health_check with additional fields
        assert health["status"] == "healthy"
        assert health["provider"] == "twilio_mock"
        assert health["timestamp"] == 1000.0
        assert "account_sid" in health
        assert "api_version" in health

    def test_generate_mock_id(self):
        """Test mock ID generation."""
        provider = TwilioMockProvider()
        
        mock_id = provider.generate_mock_id()
        
        assert mock_id.startswith("twilio_mock_")
        assert len(mock_id.split("_")[2]) == 12  # uuid4 hex[:12]

    def test_configure_error_simulation(self):
        """Test configuring error simulation rates."""
        provider = TwilioMockProvider()
        
        config = {
            "error_rate": 0.5,
            "timeout_rate": 0.1
        }
        provider.configure_error_simulation(config)
        
        assert provider.error_simulation_config["error_rate"] == 0.5
        assert provider.error_simulation_config["timeout_rate"] == 0.1
        # Other rates should remain at default
        assert provider.error_simulation_config["rate_limit_rate"] == 0.0

    @patch('random.random', return_value=0.3)
    @patch('time.sleep')
    def test_simulate_timeout_error(self, mock_sleep, mock_random):
        """Test timeout error simulation."""
        provider = TwilioMockProvider()
        provider.configure_error_simulation({"timeout_rate": 0.4})  # 0.3 < 0.4, should trigger
        
        with pytest.raises(TimeoutError, match="Provider request timed out"):
            provider.simulate_errors()
        
        mock_sleep.assert_called_once_with(30)

    @patch('random.random', return_value=0.3)
    def test_simulate_rate_limit_error(self, mock_random):
        """Test rate limit error simulation."""
        provider = TwilioMockProvider()
        provider.configure_error_simulation({"rate_limit_rate": 0.4})  # 0.3 < 0.4, should trigger
        
        with pytest.raises(ProviderRateLimitError, match="Rate limit exceeded"):
            provider.simulate_errors()

    @patch('random.random', return_value=0.2)
    def test_simulate_server_error(self, mock_random):
        """Test server error simulation."""
        provider = TwilioMockProvider()
        provider.configure_error_simulation({"server_error_rate": 0.3})  # 0.2 < 0.3, should trigger
        
        with pytest.raises(ProviderServerError, match="Internal server error"):
            provider.simulate_errors()

    @patch('random.random', return_value=0.1)
    def test_simulate_general_error(self, mock_random):
        """Test general error simulation."""
        provider = TwilioMockProvider()
        provider.configure_error_simulation({"error_rate": 0.2})  # 0.1 < 0.2, should trigger
        
        with pytest.raises(ProviderError, match="Provider error occurred"):
            provider.simulate_errors()

    @patch('random.random', return_value=0.9)
    def test_simulate_no_errors(self, mock_random):
        """Test when no errors should be simulated."""
        provider = TwilioMockProvider()
        provider.configure_error_simulation({
            "error_rate": 0.1,
            "timeout_rate": 0.1,
            "rate_limit_rate": 0.1,
            "server_error_rate": 0.1
        })  # 0.9 is higher than all rates
        
        # Should not raise any exception
        provider.simulate_errors()


class TestTwilioMockProvider:
    """Comprehensive tests for TwilioMockProvider."""

    def test_mms_message_with_attachments(self):
        """Test sending MMS message with attachments."""
        provider = TwilioMockProvider()
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "body": "MMS message",
            "type": "mms",
            "attachments": ["https://example.com/image.jpg"]
        }
        
        with patch('app.providers.twilio_mock.time.time', return_value=1000.0):
            response = provider.send_message(message_data)
        
        assert "media_url" in response
        assert response["media_url"] == ["https://example.com/image.jpg"]

    def test_validate_request_missing_field(self):
        """Test validation with missing required field."""
        provider = TwilioMockProvider()
        
        message_data = {
            "from": "+12016661234",
            # Missing "to" and "body"
        }
        
        with pytest.raises(ProviderError, match="Missing required field: to"):
            provider.validate_request(message_data)

    def test_validate_request_invalid_from_phone(self):
        """Test validation with invalid from phone number."""
        provider = TwilioMockProvider()
        
        message_data = {
            "from": "invalid_phone",
            "to": "+18045551234", 
            "body": "Test message"
        }
        
        with pytest.raises(ProviderError, match="Invalid 'from' phone number format"):
            provider.validate_request(message_data)

    def test_validate_request_invalid_to_phone(self):
        """Test validation with invalid to phone number."""
        provider = TwilioMockProvider()
        
        message_data = {
            "from": "+12016661234",
            "to": "invalid_phone",
            "body": "Test message"
        }
        
        with pytest.raises(ProviderError, match="Invalid 'to' phone number format"):
            provider.validate_request(message_data)

    def test_validate_request_body_too_long(self):
        """Test validation with body too long."""
        provider = TwilioMockProvider()
        
        long_body = "x" * 1601  # Over 1600 character limit
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "body": long_body
        }
        
        with pytest.raises(ProviderError, match="Message body must be between 1 and 1600 characters"):
            provider.validate_request(message_data)

    def test_validate_request_valid(self):
        """Test validation with valid data."""
        provider = TwilioMockProvider()
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "body": "Valid message"
        }
        
        # Should not raise any exception
        result = provider.validate_request(message_data)
        assert result is True


class TestSendGridMockProvider:
    """Comprehensive tests for SendGridMockProvider."""

    def test_validate_request_missing_field(self):
        """Test validation with missing required field."""
        provider = SendGridMockProvider()
        
        message_data = {
            "from": "sender@example.com",
            # Missing "to" and "body"
        }
        
        with pytest.raises(ProviderError, match="Missing required field: to"):
            provider.validate_request(message_data)

    def test_validate_request_invalid_from_email(self):
        """Test validation with invalid from email."""
        provider = SendGridMockProvider()
        
        message_data = {
            "from": "invalid_email",
            "to": "recipient@example.com",
            "body": "Test message"
        }
        
        with pytest.raises(ProviderError, match="Invalid 'from' email format"):
            provider.validate_request(message_data)

    def test_validate_request_invalid_to_email(self):
        """Test validation with invalid to email."""
        provider = SendGridMockProvider()
        
        message_data = {
            "from": "sender@example.com",
            "to": "invalid_email",
            "body": "Test message"
        }
        
        with pytest.raises(ProviderError, match="Invalid 'to' email format"):
            provider.validate_request(message_data)

    def test_validate_request_body_too_long(self):
        """Test validation with body too long."""
        provider = SendGridMockProvider()
        
        long_body = "x" * (1024 * 1024 + 1)  # Over 1MB limit
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": long_body
        }
        
        with pytest.raises(ProviderError, match="Message body exceeds maximum size limit"):
            provider.validate_request(message_data)

    def test_validate_request_valid(self):
        """Test validation with valid data."""
        provider = SendGridMockProvider()
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": "Valid message"
        }
        
        # Should not raise any exception
        result = provider.validate_request(message_data)
        assert result is True


class TestProviderExceptions:
    """Test provider exception classes."""

    def test_provider_error_default_status(self):
        """Test ProviderError with default status code."""
        error = ProviderError("Test error")
        assert str(error) == "Test error"
        assert error.status_code == 400

    def test_provider_error_custom_status(self):
        """Test ProviderError with custom status code."""
        error = ProviderError("Test error", status_code=422)
        assert error.status_code == 422

    def test_rate_limit_error_default_status(self):
        """Test ProviderRateLimitError with default status code."""
        error = ProviderRateLimitError("Rate limit")
        assert str(error) == "Rate limit"
        assert error.status_code == 429

    def test_server_error_default_status(self):
        """Test ProviderServerError with default status code."""
        error = ProviderServerError("Server error")
        assert str(error) == "Server error"
        assert error.status_code == 500