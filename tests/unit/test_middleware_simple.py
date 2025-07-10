"""
Simple unit tests for middleware components.
"""

import pytest
from flask import Flask
from werkzeug.exceptions import BadRequest, Unauthorized

from app.middleware.auth import require_api_key, VALID_API_KEYS
from app.middleware.validation import validate_sms_message_request, validate_email_message_request


class TestAuthMiddleware:
    """Test authentication middleware."""

    def test_valid_api_keys_exist(self):
        """Test that valid API keys are defined."""
        assert "admin_key_789" in VALID_API_KEYS
        assert "api_key_123" in VALID_API_KEYS
        assert "api_key_456" in VALID_API_KEYS

    def test_api_key_structure(self):
        """Test API key structure."""
        admin_key = VALID_API_KEYS["admin_key_789"]
        assert admin_key["user_id"] == "admin"
        assert admin_key["permissions"] == ["*"]


class TestValidationMiddleware:
    """Test validation middleware."""

    def test_validate_sms_message_request_valid(self):
        """Test SMS request validation with valid data."""
        valid_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "Test message",
            "timestamp": "2024-11-01T14:00:00Z"
        }
        
        # Should not raise exception
        result = validate_sms_message_request(valid_data)
        assert result is not None

    def test_validate_sms_message_request_missing_fields(self):
        """Test SMS request validation with missing required fields."""
        invalid_data = {
            "from": "+12016661234",
            "type": "sms"
            # Missing 'to' and 'body'
        }
        
        with pytest.raises(BadRequest):
            validate_sms_message_request(invalid_data)

    def test_validate_email_message_request_valid(self):
        """Test email request validation with valid data."""
        valid_data = {
            "from": "user@example.com",
            "to": "contact@example.com",
            "body": "Test email",
            "timestamp": "2024-11-01T14:00:00Z"
        }
        
        # Should not raise exception
        result = validate_email_message_request(valid_data)
        assert result is not None

    def test_validate_email_message_request_missing_fields(self):
        """Test email request validation with missing required fields."""
        invalid_data = {
            "from": "user@example.com"
            # Missing 'to' and 'body'
        }
        
        with pytest.raises(BadRequest):
            validate_email_message_request(invalid_data)