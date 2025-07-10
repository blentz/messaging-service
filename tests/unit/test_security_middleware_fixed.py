"""
Fixed comprehensive unit tests for security middleware to achieve 100% coverage.
"""

import pytest
import time
import base64
import hmac
import hashlib
from unittest.mock import Mock, patch

from flask import Flask
from werkzeug.exceptions import BadRequest, Unauthorized

from app.middleware.security import (
    validate_webhook_signature,
    validate_timestamp,
    validate_content_length,
    validate_content_type,
    sanitize_input,
)


class TestWebhookSignatureValidation:
    """Test webhook signature validation functionality."""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TWILIO_WEBHOOK_SECRET"] = "test_twilio_secret"
        app.config["SENDGRID_WEBHOOK_SECRET"] = "test_sendgrid_secret"
        return app

    def test_unknown_provider(self, app):
        """Test validation with unknown provider."""
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with pytest.raises(BadRequest, match="Unknown webhook provider"):
                    validate_webhook_signature("unknown_provider")
                
                mock_log.assert_called_once_with(
                    "unknown_webhook_provider",
                    severity="error",
                    provider="unknown_provider",
                    remote_addr="192.168.1.1",
                )

    def test_missing_webhook_secret_twilio(self):
        """Test validation with missing Twilio webhook secret."""
        app = Flask(__name__)
        # No TWILIO_WEBHOOK_SECRET configured
        
        with app.test_request_context('/'):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with pytest.raises(Unauthorized, match="Webhook secret not configured"):
                    validate_webhook_signature("twilio")
                
                mock_log.assert_called_once_with(
                    "missing_webhook_secret", severity="error", provider="twilio"
                )

    def test_missing_webhook_secret_sendgrid(self):
        """Test validation with missing SendGrid webhook secret."""
        app = Flask(__name__)
        # No SENDGRID_WEBHOOK_SECRET configured
        
        with app.test_request_context('/'):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with pytest.raises(Unauthorized, match="Webhook secret not configured"):
                    validate_webhook_signature("sendgrid")
                
                mock_log.assert_called_once_with(
                    "missing_webhook_secret", severity="error", provider="sendgrid"
                )

    def test_missing_signature_header_twilio(self, app):
        """Test validation with missing Twilio signature header."""
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with patch('app.middleware.security.get_metrics_manager') as mock_metrics:
                    mock_metrics_instance = Mock()
                    mock_metrics.return_value = mock_metrics_instance
                    
                    with pytest.raises(Unauthorized, match="Missing X-Twilio-Signature header"):
                        validate_webhook_signature("twilio")
                    
                    mock_log.assert_called_once_with(
                        "missing_webhook_signature",
                        severity="warning",
                        provider="twilio",
                        remote_addr="192.168.1.1",
                    )
                    mock_metrics_instance.increment_counter.assert_called_once_with(
                        "authentication_attempts_total",
                        status="missing_signature",
                        provider="twilio",
                    )

    def test_missing_signature_header_sendgrid(self, app):
        """Test validation with missing SendGrid signature header."""
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with patch('app.middleware.security.get_metrics_manager') as mock_metrics:
                    mock_metrics_instance = Mock()
                    mock_metrics.return_value = mock_metrics_instance
                    
                    with pytest.raises(Unauthorized, match="Missing X-SendGrid-Signature header"):
                        validate_webhook_signature("sendgrid")
                    
                    mock_log.assert_called_once_with(
                        "missing_webhook_signature",
                        severity="warning",
                        provider="sendgrid",
                        remote_addr="192.168.1.1",
                    )
                    mock_metrics_instance.increment_counter.assert_called_once_with(
                        "authentication_attempts_total",
                        status="missing_signature",
                        provider="sendgrid",
                    )

    def test_invalid_signature_twilio(self, app):
        """Test validation with invalid Twilio signature."""
        headers = {'X-Twilio-Signature': 'invalid_signature'}
        with app.test_request_context('/', headers=headers, data=b'test_data', 
                                     environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with patch('app.middleware.security.get_metrics_manager') as mock_metrics:
                    mock_metrics_instance = Mock()
                    mock_metrics.return_value = mock_metrics_instance
                    
                    with pytest.raises(Unauthorized, match="Invalid webhook signature"):
                        validate_webhook_signature("twilio")
                    
                    mock_log.assert_called_once_with(
                        "invalid_webhook_signature",
                        severity="warning",
                        provider="twilio",
                        provided_signature_prefix="invalid_signatur...",
                        remote_addr="192.168.1.1",
                    )
                    mock_metrics_instance.increment_counter.assert_called_once_with(
                        "authentication_attempts_total",
                        status="invalid_signature",
                        provider="twilio",
                    )

    def test_invalid_signature_sendgrid(self, app):
        """Test validation with invalid SendGrid signature."""
        headers = {'X-SendGrid-Signature': 'invalid_signature'}
        with app.test_request_context('/', headers=headers, data=b'test_data',
                                     environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with patch('app.middleware.security.get_metrics_manager') as mock_metrics:
                    mock_metrics_instance = Mock()
                    mock_metrics.return_value = mock_metrics_instance
                    
                    with pytest.raises(Unauthorized, match="Invalid webhook signature"):
                        validate_webhook_signature("sendgrid")
                    
                    mock_log.assert_called_once_with(
                        "invalid_webhook_signature",
                        severity="warning",
                        provider="sendgrid",
                        provided_signature_prefix="invalid_signatur...",
                        remote_addr="192.168.1.1",
                    )
                    mock_metrics_instance.increment_counter.assert_called_once_with(
                        "authentication_attempts_total",
                        status="invalid_signature",
                        provider="sendgrid",
                    )

    def test_valid_signature_twilio(self, app):
        """Test validation with valid Twilio signature."""
        # Generate valid Twilio signature
        secret = "test_twilio_secret"
        url = "http://localhost/"
        data = b"test_data"
        signature_payload = url.encode() + data
        
        # Twilio uses HMAC-SHA1 and base64 encoding
        expected_signature = base64.b64encode(
            hmac.new(secret.encode(), signature_payload, hashlib.sha1).digest()
        ).decode()
        
        headers = {'X-Twilio-Signature': expected_signature}
        with app.test_request_context('/', headers=headers, data=data,
                                     environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with patch('app.middleware.security.get_metrics_manager') as mock_metrics:
                    mock_metrics_instance = Mock()
                    mock_metrics.return_value = mock_metrics_instance
                    
                    # Should not raise exception
                    validate_webhook_signature("twilio")
                    
                    mock_log.assert_called_once_with(
                        "webhook_signature_validated",
                        provider="twilio",
                        remote_addr="192.168.1.1",
                    )
                    mock_metrics_instance.increment_counter.assert_called_once_with(
                        "authentication_attempts_total", status="success", provider="twilio"
                    )

    def test_valid_signature_sendgrid(self, app):
        """Test validation with valid SendGrid signature."""
        # Generate valid SendGrid signature
        secret = "test_sendgrid_secret"
        data = b"test_data"
        
        # SendGrid uses HMAC-SHA256
        expected_signature = hmac.new(
            secret.encode(), data, hashlib.sha256
        ).hexdigest()
        
        headers = {'X-SendGrid-Signature': expected_signature}
        with app.test_request_context('/', headers=headers, data=data,
                                     environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with patch('app.middleware.security.get_metrics_manager') as mock_metrics:
                    mock_metrics_instance = Mock()
                    mock_metrics.return_value = mock_metrics_instance
                    
                    # Should not raise exception
                    validate_webhook_signature("sendgrid")
                    
                    mock_log.assert_called_once_with(
                        "webhook_signature_validated",
                        provider="sendgrid",
                        remote_addr="192.168.1.1",
                    )
                    mock_metrics_instance.increment_counter.assert_called_once_with(
                        "authentication_attempts_total", status="success", provider="sendgrid"
                    )


class TestTimestampValidation:
    """Test timestamp validation functionality."""

    def test_missing_timestamp_header(self):
        """Test validation with missing timestamp header."""
        app = Flask(__name__)
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with pytest.raises(BadRequest, match="Missing X-Timestamp header"):
                    validate_timestamp()
                
                mock_log.assert_called_once_with(
                    "missing_timestamp_header",
                    severity="warning",
                    remote_addr="192.168.1.1",
                )

    def test_invalid_timestamp_format(self):
        """Test validation with invalid timestamp format."""
        app = Flask(__name__)
        headers = {'X-Timestamp': 'invalid_timestamp'}
        with app.test_request_context('/', headers=headers, environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with pytest.raises(BadRequest, match="Invalid timestamp format"):
                    validate_timestamp()
                
                mock_log.assert_called_once_with(
                    "invalid_timestamp_format",
                    severity="warning",
                    timestamp="invalid_timestamp",
                    remote_addr="192.168.1.1",
                )

    def test_timestamp_too_old(self):
        """Test validation with timestamp too old."""
        app = Flask(__name__)
        current_time = 1000
        old_timestamp = current_time - 600  # 10 minutes ago
        headers = {'X-Timestamp': str(old_timestamp)}
        
        with app.test_request_context('/', headers=headers, environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch('app.middleware.security.time.time', return_value=current_time):
                with patch('app.middleware.security.log_security_event') as mock_log:
                    with pytest.raises(BadRequest, match="Request timestamp too old"):
                        validate_timestamp(max_age_seconds=300)  # 5 minutes
                    
                    mock_log.assert_called_once_with(
                        "request_timestamp_too_old",
                        severity="warning",
                        request_time=old_timestamp,
                        current_time=current_time,
                        age_seconds=600,
                        remote_addr="192.168.1.1",
                    )

    def test_valid_timestamp(self):
        """Test validation with valid timestamp."""
        app = Flask(__name__)
        current_time = 1000
        valid_timestamp = current_time - 100  # 100 seconds ago
        headers = {'X-Timestamp': str(valid_timestamp)}
        
        with app.test_request_context('/', headers=headers):
            with patch('app.middleware.security.time.time', return_value=current_time):
                # Should not raise exception
                validate_timestamp(max_age_seconds=300)


class TestContentLengthValidation:
    """Test content length validation functionality."""

    def test_content_too_large(self):
        """Test validation with content too large."""
        app = Flask(__name__)
        large_data = b'x' * (20 * 1024 * 1024)  # 20MB
        
        with app.test_request_context('/', data=large_data, environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with pytest.raises(BadRequest, match="Request too large"):
                    validate_content_length(max_size_bytes=10 * 1024 * 1024)  # 10MB limit
                
                mock_log.assert_called_once_with(
                    "request_too_large",
                    severity="warning",
                    content_length=20 * 1024 * 1024,
                    max_size=10 * 1024 * 1024,
                    remote_addr="192.168.1.1",
                )

    def test_valid_content_length(self):
        """Test validation with valid content length."""
        app = Flask(__name__)
        small_data = b'x' * (5 * 1024 * 1024)  # 5MB
        
        with app.test_request_context('/', data=small_data):
            # Should not raise exception
            validate_content_length(max_size_bytes=10 * 1024 * 1024)

    def test_no_content_length(self):
        """Test validation with no content length."""
        app = Flask(__name__)
        
        with app.test_request_context('/'):
            # Should not raise exception
            validate_content_length()


class TestContentTypeValidation:
    """Test content type validation functionality."""

    def test_invalid_content_type(self):
        """Test validation with invalid content type."""
        app = Flask(__name__)
        headers = {'Content-Type': 'text/plain'}
        
        with app.test_request_context('/', headers=headers, environ_base={'REMOTE_ADDR': '192.168.1.1'}):
            with patch('app.middleware.security.log_security_event') as mock_log:
                with pytest.raises(BadRequest, match="Content type must be one of: application/json"):
                    validate_content_type()
                
                mock_log.assert_called_once_with(
                    "invalid_content_type",
                    severity="warning",
                    content_type="text/plain",
                    allowed_types=["application/json"],
                    remote_addr="192.168.1.1",
                )

    def test_valid_content_type_default(self):
        """Test validation with valid default content type."""
        app = Flask(__name__)
        headers = {'Content-Type': 'application/json'}
        
        with app.test_request_context('/', headers=headers):
            # Should not raise exception
            validate_content_type()

    def test_valid_content_type_custom(self):
        """Test validation with valid custom content type."""
        app = Flask(__name__)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        with app.test_request_context('/', headers=headers):
            # Should not raise exception
            validate_content_type(
                allowed_types=["application/json", "application/x-www-form-urlencoded"]
            )


class TestInputSanitization:
    """Test input sanitization functionality."""

    def test_sanitize_non_dict(self):
        """Test sanitization of non-dictionary input."""
        result = sanitize_input("string")
        assert result == "string"

    def test_sanitize_empty_dict(self):
        """Test sanitization of empty dictionary."""
        result = sanitize_input({})
        assert result == {}

    def test_sanitize_script_tags(self):
        """Test sanitization of script tags."""
        data = {"message": "<script>alert('xss')</script>Hello world"}
        result = sanitize_input(data)
        assert result["message"] == "Hello world"

    def test_sanitize_iframe_tags(self):
        """Test sanitization of iframe tags."""
        data = {"content": "<iframe src='evil.com'></iframe>Safe content"}
        result = sanitize_input(data)
        assert result["content"] == "Safe content"

    def test_sanitize_javascript_protocol(self):
        """Test sanitization of javascript protocol."""
        data = {"link": "javascript:alert('xss')"}
        result = sanitize_input(data)
        assert result["link"] == "alert('xss')"

    def test_sanitize_case_insensitive(self):
        """Test case-insensitive sanitization."""
        data = {"code": "<SCRIPT>alert('XSS')</SCRIPT>"}
        result = sanitize_input(data)
        assert result["code"] == ""

    def test_sanitize_long_string(self):
        """Test sanitization of overly long strings."""
        long_string = "x" * 15000
        data = {"long_field": long_string}
        
        with patch('app.middleware.security.log_security_event') as mock_log:
            result = sanitize_input(data)
            
            assert len(result["long_field"]) == 10000
            mock_log.assert_called_once_with(
                "input_string_too_long",
                severity="warning",
                field="long_field",
                length=15000,
            )

    def test_sanitize_nested_dict(self):
        """Test sanitization of nested dictionaries."""
        data = {
            "user": {
                "name": "<script>alert('xss')</script>John",
                "email": "john@example.com"
            }
        }
        result = sanitize_input(data)
        assert result["user"]["name"] == "John"
        assert result["user"]["email"] == "john@example.com"

    def test_sanitize_list_with_dicts(self):
        """Test sanitization of lists containing dictionaries."""
        data = {
            "items": [
                {"name": "<script>alert('xss')</script>Item1"},
                {"name": "Item2"},
                "simple_string"
            ]
        }
        result = sanitize_input(data)
        assert result["items"][0]["name"] == "Item1"
        assert result["items"][1]["name"] == "Item2"
        assert result["items"][2] == "simple_string"

    def test_sanitize_complex_nested_structure(self):
        """Test sanitization of complex nested structures."""
        data = {
            "level1": {
                "level2": [
                    {
                        "dangerous": "<iframe src='evil.com'></iframe>Safe",
                        "safe": "Clean content"
                    }
                ]
            }
        }
        result = sanitize_input(data)
        assert result["level1"]["level2"][0]["dangerous"] == "Safe"
        assert result["level1"]["level2"][0]["safe"] == "Clean content"