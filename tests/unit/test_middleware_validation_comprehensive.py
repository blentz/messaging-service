"""
Comprehensive tests for middleware validation to achieve 100% coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
from werkzeug.exceptions import BadRequest

from app.middleware.validation import (
    validate_sms_message_request,
    validate_email_message_request,
    validate_sms_webhook_request,
    validate_email_webhook_request,
    validate_pagination_params,
    _is_valid_url,
    _is_valid_iso_timestamp,
)


class TestSMSMessageValidation:
    """Test SMS message validation comprehensive coverage."""

    def test_missing_required_fields(self):
        """Test missing required fields."""
        # Missing 'from'
        with pytest.raises(BadRequest, match="Missing required field: from"):
            validate_sms_message_request({"to": "+18045551234", "type": "sms", "body": "test"})
        
        # Missing 'to'
        with pytest.raises(BadRequest, match="Missing required field: to"):
            validate_sms_message_request({"from": "+12016661234", "type": "sms", "body": "test"})
        
        # Missing 'type'
        with pytest.raises(BadRequest, match="Missing required field: type"):
            validate_sms_message_request({"from": "+12016661234", "to": "+18045551234", "body": "test"})
        
        # Missing 'body'
        with pytest.raises(BadRequest, match="Missing required field: body"):
            validate_sms_message_request({"from": "+12016661234", "to": "+18045551234", "type": "sms"})

    @patch('app.middleware.validation.log_security_event')
    def test_invalid_from_phone_format(self, mock_log_security):
        """Test invalid 'from' phone number format with security logging."""
        data = {"from": "invalid", "to": "+18045551234", "type": "sms", "body": "test"}
        
        with pytest.raises(BadRequest, match="Invalid 'from' phone number format"):
            validate_sms_message_request(data)
        
        # Verify security event was logged
        mock_log_security.assert_called_once_with(
            "invalid_phone_number_format",
            field="from",
            value="inval...",
            expected_format="E.164"
        )

    @patch('app.middleware.validation.log_security_event')
    def test_invalid_to_phone_format(self, mock_log_security):
        """Test invalid 'to' phone number format with security logging."""
        data = {"from": "+12016661234", "to": "1234567890", "type": "sms", "body": "test"}
        
        with pytest.raises(BadRequest, match="Invalid 'to' phone number format"):
            validate_sms_message_request(data)
        
        # Verify security event was logged
        mock_log_security.assert_called_once_with(
            "invalid_phone_number_format",
            field="to",
            value="12345...",
            expected_format="E.164"
        )

    def test_invalid_message_type(self):
        """Test invalid message type."""
        data = {"from": "+12016661234", "to": "+18045551234", "type": "invalid", "body": "test"}
        
        with pytest.raises(BadRequest, match="Message type must be 'sms' or 'mms'"):
            validate_sms_message_request(data)

    def test_invalid_body_empty(self):
        """Test empty message body."""
        data = {"from": "+12016661234", "to": "+18045551234", "type": "sms", "body": ""}
        
        with pytest.raises(BadRequest, match="Message body must be between 1 and 1600 characters"):
            validate_sms_message_request(data)

    def test_invalid_body_too_long(self):
        """Test message body too long."""
        data = {"from": "+12016661234", "to": "+18045551234", "type": "sms", "body": "A" * 1601}
        
        with pytest.raises(BadRequest, match="Message body must be between 1 and 1600 characters"):
            validate_sms_message_request(data)

    def test_mms_with_too_many_attachments(self):
        """Test MMS with too many attachments."""
        data = {
            "from": "+12016661234",
            "to": "+18045551234", 
            "type": "mms",
            "body": "test",
            "attachments": [f"https://example.com/image{i}.jpg" for i in range(11)]
        }
        
        with pytest.raises(BadRequest, match="MMS messages cannot have more than 10 attachments"):
            validate_sms_message_request(data)

    def test_mms_with_invalid_attachment_url(self):
        """Test MMS with invalid attachment URL."""
        data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "mms", 
            "body": "test",
            "attachments": ["invalid-url"]
        }
        
        with pytest.raises(BadRequest, match="Invalid attachment URL: invalid-url"):
            validate_sms_message_request(data)

    def test_invalid_timestamp_format(self):
        """Test invalid timestamp format."""
        data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "test",
            "timestamp": "invalid-timestamp"
        }
        
        with pytest.raises(BadRequest, match="Invalid timestamp format. Must be ISO 8601."):
            validate_sms_message_request(data)

    def test_valid_sms_with_timestamp(self):
        """Test valid SMS with timestamp."""
        data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "test",
            "timestamp": "2025-07-10T10:00:00Z"
        }
        
        result = validate_sms_message_request(data)
        assert result == data

    def test_valid_mms_with_attachments(self):
        """Test valid MMS with attachments."""
        data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "mms",
            "body": "test",
            "attachments": ["https://example.com/image.jpg"]
        }
        
        result = validate_sms_message_request(data)
        assert result == data


class TestEmailMessageValidation:
    """Test email message validation comprehensive coverage."""

    def test_missing_required_fields(self):
        """Test missing required fields."""
        # Missing 'from'
        with pytest.raises(BadRequest, match="Missing required field: from"):
            validate_email_message_request({"to": "test@example.com", "body": "test"})
        
        # Missing 'to'
        with pytest.raises(BadRequest, match="Missing required field: to"):
            validate_email_message_request({"from": "sender@example.com", "body": "test"})
        
        # Missing 'body'
        with pytest.raises(BadRequest, match="Missing required field: body"):
            validate_email_message_request({"from": "sender@example.com", "to": "test@example.com"})

    @patch('app.middleware.validation.log_security_event')
    def test_invalid_from_email_format(self, mock_log_security):
        """Test invalid 'from' email format with security logging."""
        data = {"from": "invalid-email", "to": "test@example.com", "body": "test"}
        
        with pytest.raises(BadRequest, match="Invalid 'from' email address format"):
            validate_email_message_request(data)
        
        # Verify security event was logged
        mock_log_security.assert_called_once_with(
            "invalid_email_format",
            field="from",
            value="invalid-email"
        )

    @patch('app.middleware.validation.log_security_event')
    def test_invalid_to_email_format(self, mock_log_security):
        """Test invalid 'to' email format with security logging."""
        data = {"from": "sender@example.com", "to": "invalid-email", "body": "test"}
        
        with pytest.raises(BadRequest, match="Invalid 'to' email address format"):
            validate_email_message_request(data)
        
        # Verify security event was logged
        mock_log_security.assert_called_once_with(
            "invalid_email_format", 
            field="to",
            value="invalid-email"
        )

    def test_empty_body(self):
        """Test empty message body."""
        data = {"from": "sender@example.com", "to": "test@example.com", "body": ""}
        
        with pytest.raises(BadRequest, match="Message body cannot be empty"):
            validate_email_message_request(data)

    def test_body_too_large(self):
        """Test message body exceeds size limit."""
        data = {
            "from": "sender@example.com",
            "to": "test@example.com", 
            "body": "A" * (1024 * 1024 + 1)  # 1MB + 1 byte
        }
        
        with pytest.raises(BadRequest, match="Message body exceeds maximum size limit"):
            validate_email_message_request(data)

    def test_too_many_email_attachments(self):
        """Test email with too many attachments."""
        data = {
            "from": "sender@example.com",
            "to": "test@example.com",
            "body": "test",
            "attachments": [f"https://example.com/file{i}.pdf" for i in range(26)]
        }
        
        with pytest.raises(BadRequest, match="Email messages cannot have more than 25 attachments"):
            validate_email_message_request(data)

    def test_email_with_invalid_attachment_url(self):
        """Test email with invalid attachment URL."""
        data = {
            "from": "sender@example.com",
            "to": "test@example.com",
            "body": "test",
            "attachments": ["invalid-url"]
        }
        
        with pytest.raises(BadRequest, match="Invalid attachment URL: invalid-url"):
            validate_email_message_request(data)

    def test_email_invalid_timestamp(self):
        """Test email with invalid timestamp."""
        data = {
            "from": "sender@example.com",
            "to": "test@example.com",
            "body": "test",
            "timestamp": "not-iso-8601"
        }
        
        with pytest.raises(BadRequest, match="Invalid timestamp format. Must be ISO 8601."):
            validate_email_message_request(data)

    def test_valid_email_with_attachments(self):
        """Test valid email with attachments."""
        data = {
            "from": "sender@example.com",
            "to": "test@example.com",
            "body": "test message",
            "attachments": ["https://example.com/file.pdf"],
            "timestamp": "2025-07-10T10:00:00.000Z"
        }
        
        result = validate_email_message_request(data)
        assert result == data


class TestSMSWebhookValidation:
    """Test SMS webhook validation comprehensive coverage."""

    def test_missing_required_fields(self):
        """Test missing required webhook fields."""
        # Missing 'from'
        with pytest.raises(BadRequest, match="Missing required field: from"):
            validate_sms_webhook_request({"to": "+18045551234", "type": "sms", "messaging_provider_id": "msg-123", "body": "test"})
        
        # Missing 'messaging_provider_id'
        with pytest.raises(BadRequest, match="Missing required field: messaging_provider_id"):
            validate_sms_webhook_request({"from": "+12016661234", "to": "+18045551234", "type": "sms", "body": "test"})

    def test_invalid_phone_numbers(self):
        """Test invalid phone numbers in webhook."""
        # Invalid 'from'
        with pytest.raises(BadRequest, match="Invalid 'from' phone number format"):
            validate_sms_webhook_request({
                "from": "invalid",
                "to": "+18045551234",
                "type": "sms",
                "messaging_provider_id": "msg-123",
                "body": "test"
            })
        
        # Invalid 'to'
        with pytest.raises(BadRequest, match="Invalid 'to' phone number format"):
            validate_sms_webhook_request({
                "from": "+12016661234",
                "to": "invalid", 
                "type": "sms",
                "messaging_provider_id": "msg-123",
                "body": "test"
            })

    def test_invalid_message_type_webhook(self):
        """Test invalid message type in webhook."""
        with pytest.raises(BadRequest, match="Message type must be 'sms' or 'mms'"):
            validate_sms_webhook_request({
                "from": "+12016661234",
                "to": "+18045551234",
                "type": "invalid",
                "messaging_provider_id": "msg-123", 
                "body": "test"
            })

    def test_empty_provider_id(self):
        """Test empty messaging provider ID."""
        with pytest.raises(BadRequest, match="messaging_provider_id cannot be empty"):
            validate_sms_webhook_request({
                "from": "+12016661234",
                "to": "+18045551234",
                "type": "sms",
                "messaging_provider_id": "",
                "body": "test"
            })

    def test_valid_sms_webhook(self):
        """Test valid SMS webhook."""
        data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "messaging_provider_id": "msg-123",
            "body": "test"
        }
        
        result = validate_sms_webhook_request(data)
        assert result == data


class TestEmailWebhookValidation:
    """Test email webhook validation comprehensive coverage."""

    def test_missing_required_fields(self):
        """Test missing required webhook fields."""
        # Missing 'xillio_id'
        with pytest.raises(BadRequest, match="Missing required field: xillio_id"):
            validate_email_webhook_request({"from": "sender@example.com", "to": "test@example.com", "body": "test"})

    def test_invalid_email_addresses_webhook(self):
        """Test invalid email addresses in webhook."""
        # Invalid 'from'
        with pytest.raises(BadRequest, match="Invalid 'from' email address format"):
            validate_email_webhook_request({
                "from": "invalid",
                "to": "test@example.com",
                "xillio_id": "email-123",
                "body": "test"
            })
        
        # Invalid 'to'
        with pytest.raises(BadRequest, match="Invalid 'to' email address format"):
            validate_email_webhook_request({
                "from": "sender@example.com",
                "to": "invalid",
                "xillio_id": "email-123",
                "body": "test"
            })

    def test_empty_xillio_id(self):
        """Test empty xillio_id."""
        with pytest.raises(BadRequest, match="xillio_id cannot be empty"):
            validate_email_webhook_request({
                "from": "sender@example.com",
                "to": "test@example.com",
                "xillio_id": "",
                "body": "test"
            })

    def test_valid_email_webhook(self):
        """Test valid email webhook."""
        data = {
            "from": "sender@example.com",
            "to": "test@example.com",
            "xillio_id": "email-123",
            "body": "test"
        }
        
        result = validate_email_webhook_request(data)
        assert result == data


class TestPaginationValidation:
    """Test pagination validation comprehensive coverage."""

    def test_default_values(self):
        """Test default pagination values."""
        limit, offset = validate_pagination_params()
        assert limit == 50
        assert offset == 0

    def test_limit_below_minimum(self):
        """Test limit below minimum."""
        with pytest.raises(BadRequest, match="Limit must be between 1 and 1000"):
            validate_pagination_params(limit=0)

    def test_limit_above_maximum(self):
        """Test limit above maximum."""
        with pytest.raises(BadRequest, match="Limit must be between 1 and 1000"):
            validate_pagination_params(limit=1001)

    def test_invalid_limit_string(self):
        """Test invalid limit string."""
        with pytest.raises(BadRequest, match="Limit must be a valid integer"):
            validate_pagination_params(limit="invalid")

    def test_invalid_limit_float(self):
        """Test invalid limit float."""
        # Float values will be converted to int, so 12.5 becomes 12 which is valid
        limit, offset = validate_pagination_params(limit=12.5)
        assert limit == 12
        assert offset == 0

    def test_negative_offset(self):
        """Test negative offset."""
        with pytest.raises(BadRequest, match="Offset must be non-negative"):
            validate_pagination_params(offset=-1)

    def test_invalid_offset_string(self):
        """Test invalid offset string."""
        with pytest.raises(BadRequest, match="Offset must be a valid integer"):
            validate_pagination_params(offset="invalid")

    def test_invalid_offset_float(self):
        """Test invalid offset float."""
        # Float values will be converted to int, so 12.5 becomes 12 which is valid
        limit, offset = validate_pagination_params(offset=12.5)
        assert limit == 50  # default
        assert offset == 12

    def test_valid_pagination_params(self):
        """Test valid pagination parameters."""
        limit, offset = validate_pagination_params(limit=25, offset=100)
        assert limit == 25
        assert offset == 100

    def test_string_number_conversion(self):
        """Test string number conversion."""
        limit, offset = validate_pagination_params(limit="25", offset="100")
        assert limit == 25
        assert offset == 100


class TestHelperFunctions:
    """Test helper functions comprehensive coverage."""

    def test_is_valid_url_valid_cases(self):
        """Test valid URL cases."""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://example.com/path/to/file.jpg",
            "https://subdomain.example.com/file.pdf",
            "http://example.com:8080/api"
        ]
        
        for url in valid_urls:
            assert _is_valid_url(url), f"URL should be valid: {url}"

    def test_is_valid_url_invalid_cases(self):
        """Test invalid URL cases."""
        invalid_urls = [
            "ftp://example.com",  # Wrong protocol
            "not-a-url",
            "",
            "https://",
            "example.com",  # Missing protocol
            "https:// example.com",  # Space
        ]
        
        for url in invalid_urls:
            assert not _is_valid_url(url), f"URL should be invalid: {url}"

    def test_is_valid_iso_timestamp_valid_cases(self):
        """Test valid ISO timestamp cases."""
        valid_timestamps = [
            "2025-07-10T10:00:00Z",
            "2025-07-10T10:00:00.123Z",
            "2025-07-10T10:00:00+00:00",
        ]
        
        for timestamp in valid_timestamps:
            assert _is_valid_iso_timestamp(timestamp), f"Timestamp should be valid: {timestamp}"

    def test_is_valid_iso_timestamp_invalid_cases(self):
        """Test invalid ISO timestamp cases."""
        invalid_timestamps = [
            "invalid",
            "",
            "2025-07-10",
            "2025-07-10 10:00:00",
            "2025-13-10T10:00:00Z",  # Invalid month
        ]
        
        for timestamp in invalid_timestamps:
            assert not _is_valid_iso_timestamp(timestamp), f"Timestamp should be invalid: {timestamp}"

    def test_is_valid_iso_timestamp_exception_handling(self):
        """Test ISO timestamp exception handling."""
        # Test with an invalid timestamp that triggers ValueError in strptime
        # The function already handles all exceptions and returns False
        result = _is_valid_iso_timestamp("invalid-timestamp-format")
        assert result is False