"""
Service for managing provider integrations and routing.
"""

import time

from app.providers.base import ProviderError
from app.providers.sendgrid_mock import SendGridMockProvider
from app.providers.twilio_mock import TwilioMockProvider
from app.utils.logging import get_logger, log_provider_event
from app.utils.metrics import get_metrics_manager


class ProviderService:
    """Service for routing messages to appropriate providers."""

    def __init__(self):
        self.logger = get_logger()
        self.metrics = get_metrics_manager()
        self.twilio_provider = TwilioMockProvider()
        self.sendgrid_provider = SendGridMockProvider()

    def send_sms_message(self, message_data: dict) -> dict:
        """
        Send SMS/MMS message through Twilio mock provider.

        Args:
            message_data: Message data dict

        Returns:
            Provider response dict
        """
        start_time = time.time()

        try:
            log_provider_event(
                "sending_sms_message",
                provider_name="twilio_mock",
                message_type=message_data.get("type"),
                from_address=message_data.get("from"),
                to_address=message_data.get("to"),
            )

            response = self.twilio_provider.send_message(message_data)

            duration = time.time() - start_time
            self.metrics.record_histogram(
                "provider_response_duration_seconds",
                duration,
                provider="twilio_mock",
                message_type=message_data.get("type"),
            )

            log_provider_event(
                "sms_message_sent_successfully",
                provider_name="twilio_mock",
                provider_id=response.get("sid"),
                status=response.get("status"),
            )

            return response

        except ProviderError:
            # Re-raise ProviderError to maintain proper status codes
            raise
        except Exception as e:
            duration = time.time() - start_time
            self.metrics.record_histogram(
                "provider_response_duration_seconds",
                duration,
                provider="twilio_mock",
                message_type=message_data.get("type"),
                status="error",
            )
            self.metrics.increment_counter(
                "provider_errors_total",
                provider="twilio_mock",
                error_type=type(e).__name__,
            )

            log_provider_event(
                "sms_message_send_failed",
                provider_name="twilio_mock",
                error=str(e),
                message_data=message_data,
            )
            raise

    def send_email_message(self, message_data: dict) -> dict:
        """
        Send email message through SendGrid mock provider.

        Args:
            message_data: Message data dict

        Returns:
            Provider response dict
        """
        start_time = time.time()

        try:
            log_provider_event(
                "sending_email_message",
                provider_name="sendgrid_mock",
                from_address=message_data.get("from"),
                to_address=message_data.get("to"),
            )

            response = self.sendgrid_provider.send_message(message_data)

            duration = time.time() - start_time
            self.metrics.record_histogram(
                "provider_response_duration_seconds",
                duration,
                provider="sendgrid_mock",
                message_type="email",
            )

            log_provider_event(
                "email_message_sent_successfully",
                provider_name="sendgrid_mock",
                message_id=response.get("message_id"),
                status=response.get("status"),
            )

            return response

        except ProviderError:
            # Re-raise ProviderError to maintain proper status codes
            raise
        except Exception as e:
            duration = time.time() - start_time
            self.metrics.record_histogram(
                "provider_response_duration_seconds",
                duration,
                provider="sendgrid_mock",
                message_type="email",
                status="error",
            )
            self.metrics.increment_counter(
                "provider_errors_total",
                provider="sendgrid_mock",
                error_type=type(e).__name__,
            )

            log_provider_event(
                "email_message_send_failed",
                provider_name="sendgrid_mock",
                error=str(e),
                message_data=message_data,
            )
            raise
