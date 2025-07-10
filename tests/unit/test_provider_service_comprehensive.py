"""
Comprehensive unit tests for ProviderService to achieve 100% coverage.
"""

import pytest
from unittest.mock import Mock, patch

from app.services.provider_service import ProviderService
from app.providers.base import ProviderError


class TestProviderService:
    """Comprehensive test suite for ProviderService."""

    @pytest.fixture
    def provider_service(self):
        return ProviderService()

    def test_service_initialization(self, provider_service):
        """Test service initializes correctly."""
        assert provider_service is not None
        assert provider_service.logger is not None
        assert provider_service.metrics is not None
        assert provider_service.twilio_provider is not None
        assert provider_service.sendgrid_provider is not None

    @patch('app.services.provider_service.time.time')
    @patch('app.services.provider_service.log_provider_event')
    def test_send_sms_message_success(self, mock_log_provider, mock_time, provider_service):
        """Test successful SMS message sending."""
        # Setup mocks
        mock_time.return_value = 1000.0
        mock_response = {"sid": "SM123456", "status": "sent"}
        provider_service.twilio_provider.send_message = Mock(return_value=mock_response)
        provider_service.metrics.record_histogram = Mock()
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "Test message"
        }
        
        result = provider_service.send_sms_message(message_data)
        
        # Verify result
        assert result == mock_response
        
        # Verify provider was called
        provider_service.twilio_provider.send_message.assert_called_once_with(message_data)
        
        # Verify logging calls
        assert mock_log_provider.call_count == 2
        mock_log_provider.assert_any_call(
            "sending_sms_message",
            provider_name="twilio_mock",
            message_type="sms",
            from_address="+12016661234",
            to_address="+18045551234",
        )
        mock_log_provider.assert_any_call(
            "sms_message_sent_successfully",
            provider_name="twilio_mock",
            provider_id="SM123456",
            status="sent",
        )
        
        # Verify metrics recording
        provider_service.metrics.record_histogram.assert_called_once()

    @patch('app.services.provider_service.time.time')
    @patch('app.services.provider_service.log_provider_event')
    def test_send_sms_message_provider_error(self, mock_log_provider, mock_time, provider_service):
        """Test SMS message sending with provider error."""
        # Setup mocks
        mock_time.return_value = 1000.0
        provider_error = ProviderError("Twilio service unavailable", 503)
        provider_service.twilio_provider.send_message = Mock(side_effect=provider_error)
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "Test message"
        }
        
        # Test that ProviderError is re-raised
        with pytest.raises(ProviderError):
            provider_service.send_sms_message(message_data)
        
        # Verify initial logging call
        mock_log_provider.assert_called_once_with(
            "sending_sms_message",
            provider_name="twilio_mock",
            message_type="sms",
            from_address="+12016661234",
            to_address="+18045551234",
        )

    @patch('app.services.provider_service.time.time')
    @patch('app.services.provider_service.log_provider_event')
    def test_send_sms_message_general_exception(self, mock_log_provider, mock_time, provider_service):
        """Test SMS message sending with general exception."""
        # Setup mocks
        mock_time.side_effect = [1000.0, 1005.0]  # start and end times
        general_error = Exception("Network timeout")
        provider_service.twilio_provider.send_message = Mock(side_effect=general_error)
        provider_service.metrics.record_histogram = Mock()
        provider_service.metrics.increment_counter = Mock()
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "Test message"
        }
        
        # Test that general exception is re-raised
        with pytest.raises(Exception, match="Network timeout"):
            provider_service.send_sms_message(message_data)
        
        # Verify error metrics recording
        provider_service.metrics.record_histogram.assert_called_once_with(
            "provider_response_duration_seconds",
            5.0,  # 1005.0 - 1000.0
            provider="twilio_mock",
            message_type="sms",
            status="error",
        )
        provider_service.metrics.increment_counter.assert_called_once_with(
            "provider_errors_total",
            provider="twilio_mock",
            error_type="Exception",
        )
        
        # Verify error logging
        assert mock_log_provider.call_count == 2
        mock_log_provider.assert_any_call(
            "sms_message_send_failed",
            provider_name="twilio_mock",
            error="Network timeout",
            message_data=message_data,
        )

    @patch('app.services.provider_service.time.time')
    @patch('app.services.provider_service.log_provider_event')
    def test_send_email_message_success(self, mock_log_provider, mock_time, provider_service):
        """Test successful email message sending."""
        # Setup mocks
        mock_time.return_value = 2000.0
        mock_response = {"message_id": "email-123", "status": "sent"}
        provider_service.sendgrid_provider.send_message = Mock(return_value=mock_response)
        provider_service.metrics.record_histogram = Mock()
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": "Test email message"
        }
        
        result = provider_service.send_email_message(message_data)
        
        # Verify result
        assert result == mock_response
        
        # Verify provider was called
        provider_service.sendgrid_provider.send_message.assert_called_once_with(message_data)
        
        # Verify logging calls
        assert mock_log_provider.call_count == 2
        mock_log_provider.assert_any_call(
            "sending_email_message",
            provider_name="sendgrid_mock",
            from_address="sender@example.com",
            to_address="recipient@example.com",
        )
        mock_log_provider.assert_any_call(
            "email_message_sent_successfully",
            provider_name="sendgrid_mock",
            message_id="email-123",
            status="sent",
        )
        
        # Verify metrics recording
        provider_service.metrics.record_histogram.assert_called_once()

    @patch('app.services.provider_service.time.time')
    @patch('app.services.provider_service.log_provider_event')
    def test_send_email_message_provider_error(self, mock_log_provider, mock_time, provider_service):
        """Test email message sending with provider error."""
        # Setup mocks
        mock_time.return_value = 2000.0
        provider_error = ProviderError("SendGrid rate limit exceeded", 429)
        provider_service.sendgrid_provider.send_message = Mock(side_effect=provider_error)
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": "Test email message"
        }
        
        # Test that ProviderError is re-raised
        with pytest.raises(ProviderError):
            provider_service.send_email_message(message_data)
        
        # Verify initial logging call
        mock_log_provider.assert_called_once_with(
            "sending_email_message",
            provider_name="sendgrid_mock",
            from_address="sender@example.com",
            to_address="recipient@example.com",
        )

    @patch('app.services.provider_service.time.time')
    @patch('app.services.provider_service.log_provider_event')
    def test_send_email_message_general_exception(self, mock_log_provider, mock_time, provider_service):
        """Test email message sending with general exception."""
        # Setup mocks
        mock_time.side_effect = [2000.0, 2003.0]  # start and end times
        general_error = ConnectionError("SendGrid connection failed")
        provider_service.sendgrid_provider.send_message = Mock(side_effect=general_error)
        provider_service.metrics.record_histogram = Mock()
        provider_service.metrics.increment_counter = Mock()
        
        message_data = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "body": "Test email message"
        }
        
        # Test that general exception is re-raised
        with pytest.raises(ConnectionError, match="SendGrid connection failed"):
            provider_service.send_email_message(message_data)
        
        # Verify error metrics recording
        provider_service.metrics.record_histogram.assert_called_once_with(
            "provider_response_duration_seconds",
            3.0,  # 2003.0 - 2000.0
            provider="sendgrid_mock",
            message_type="email",
            status="error",
        )
        provider_service.metrics.increment_counter.assert_called_once_with(
            "provider_errors_total",
            provider="sendgrid_mock",
            error_type="ConnectionError",
        )
        
        # Verify error logging
        assert mock_log_provider.call_count == 2
        mock_log_provider.assert_any_call(
            "email_message_send_failed",
            provider_name="sendgrid_mock",
            error="SendGrid connection failed",
            message_data=message_data,
        )

    @patch('app.services.provider_service.time.time')
    @patch('app.services.provider_service.log_provider_event')
    def test_send_sms_message_mms_type(self, mock_log_provider, mock_time, provider_service):
        """Test sending MMS message through SMS service."""
        # Setup mocks
        mock_time.return_value = 1500.0
        mock_response = {"sid": "MM789012", "status": "sent"}
        provider_service.twilio_provider.send_message = Mock(return_value=mock_response)
        provider_service.metrics.record_histogram = Mock()
        
        message_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "mms",
            "body": "Test MMS",
            "attachments": ["https://example.com/image.jpg"]
        }
        
        result = provider_service.send_sms_message(message_data)
        
        # Verify result
        assert result == mock_response
        
        # Verify MMS type is properly logged
        mock_log_provider.assert_any_call(
            "sending_sms_message",
            provider_name="twilio_mock",
            message_type="mms",
            from_address="+12016661234",
            to_address="+18045551234",
        )

    @patch('app.services.provider_service.time.time')
    @patch('app.services.provider_service.log_provider_event')
    def test_send_message_with_missing_data_fields(self, mock_log_provider, mock_time, provider_service):
        """Test sending messages with missing data fields."""
        # Setup mocks
        mock_time.return_value = 3000.0
        mock_response = {"sid": "SM999999", "status": "sent"}
        provider_service.twilio_provider.send_message = Mock(return_value=mock_response)
        provider_service.metrics.record_histogram = Mock()
        
        # Message data with missing fields (using .get() should handle gracefully)
        message_data = {
            "body": "Message with minimal data"
            # Missing from, to, type fields
        }
        
        result = provider_service.send_sms_message(message_data)
        
        # Verify result
        assert result == mock_response
        
        # Verify logging handles None values gracefully
        mock_log_provider.assert_any_call(
            "sending_sms_message",
            provider_name="twilio_mock",
            message_type=None,
            from_address=None,
            to_address=None,
        )