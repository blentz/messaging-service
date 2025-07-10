"""
API endpoints for receiving webhooks from message providers.
"""

import time

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import Unauthorized

from app.middleware.security import (
    sanitize_input,
    validate_content_length,
    validate_content_type,
    validate_webhook_signature,
)
from app.middleware.validation import (
    validate_email_webhook_request,
    validate_sms_webhook_request,
)
from app.services.message_service import MessageService
from app.utils.logging import get_logger
from app.utils.metrics import get_metrics_manager

webhooks_bp = Blueprint("webhooks", __name__)
logger = get_logger()
metrics = get_metrics_manager()


@webhooks_bp.route("/webhooks/sms", methods=["POST"])
def receive_sms_webhook():
    """
    Receive SMS/MMS webhook from provider.

    POST /api/webhooks/sms

    Request body:
    {
        "from": "+18045551234",
        "to": "+12016661234",
        "type": "sms" | "mms",
        "messaging_provider_id": "message-1",
        "body": "text message",
        "attachments": ["attachment-url"] | [] | null,
        "timestamp": "2024-11-01T14:00:00Z"
    }

    Response:
    {
        "status": "processed",
        "message_id": 123
    }
    """
    start_time = time.time()

    try:
        # Validate security
        validate_webhook_signature("twilio")
        validate_content_type(["application/json", "application/x-www-form-urlencoded"])
        validate_content_length()

        # Get and sanitize request data
        if request.content_type == "application/json":
            data = request.get_json()
        else:
            # Convert form data to JSON format for Twilio webhooks
            data = request.form.to_dict()
            # Normalize Twilio webhook field names
            data = {
                "from": data.get("From"),
                "to": data.get("To"),
                "type": "sms" if data.get("NumMedia", "0") == "0" else "mms",
                "messaging_provider_id": data.get("MessageSid"),
                "body": data.get("Body", ""),
                "attachments": [data.get("MediaUrl0")] if data.get("MediaUrl0") else [],
                "timestamp": data.get("DateCreated"),
            }

        if not data:
            return jsonify({"error": "Request body required"}), 400

        data = sanitize_input(data)
        data = validate_sms_webhook_request(data)

        # Process webhook
        message_service = MessageService()
        result = message_service.process_inbound_sms_webhook(data)

        # Track metrics
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="webhooks_sms",
            status="success",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="webhooks_sms",
        )

        logger.info(
            "SMS webhook processed successfully",
            message_id=result["message_id"],
            provider_id=data["messaging_provider_id"],
            message_type=data["type"],
        )

        return jsonify(result), 200

    except ValueError as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="webhooks_sms",
            status="validation_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="webhooks_sms",
            status="error",
        )

        logger.warning("SMS webhook validation failed", error=str(e))
        return jsonify({"error": str(e)}), 400

    except Unauthorized as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="webhooks_sms",
            status="unauthorized",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="webhooks_sms",
            status="error",
        )

        logger.warning("SMS webhook authentication failed", error=str(e))
        return jsonify({"error": str(e)}), 401

    except Exception as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="webhooks_sms",
            status="server_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="webhooks_sms",
            status="error",
        )

        logger.error("Failed to process SMS webhook", error=str(e))
        return jsonify({"error": "Internal server error"}), 500


@webhooks_bp.route("/webhooks/email", methods=["POST"])
def receive_email_webhook():
    """
    Receive email webhook from provider.

    POST /api/webhooks/email

    Request body:
    {
        "from": "user@usehatchapp.com",
        "to": "contact@gmail.com",
        "xillio_id": "message-2",
        "body": "<html><body>html is <b>allowed</b> here</body></html>",
        "attachments": ["attachment-url"] | [],
        "timestamp": "2024-11-01T14:00:00Z"
    }

    Response:
    {
        "status": "processed",
        "message_id": 123
    }
    """
    start_time = time.time()

    try:
        # Validate security
        validate_webhook_signature("sendgrid")
        validate_content_type(["application/json"])
        validate_content_length()

        # Get and sanitize request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400

        data = sanitize_input(data)
        data = validate_email_webhook_request(data)

        # Process webhook
        message_service = MessageService()
        result = message_service.process_inbound_email_webhook(data)

        # Track metrics
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="webhooks_email",
            status="success",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="webhooks_email",
        )

        logger.info(
            "Email webhook processed successfully",
            message_id=result["message_id"],
            provider_id=data["xillio_id"],
        )

        return jsonify(result), 200

    except ValueError as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="webhooks_email",
            status="validation_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="webhooks_email",
            status="error",
        )

        logger.warning("Email webhook validation failed", error=str(e))
        return jsonify({"error": str(e)}), 400

    except Unauthorized as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="webhooks_email",
            status="unauthorized",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="webhooks_email",
            status="error",
        )

        logger.warning("Email webhook authentication failed", error=str(e))
        return jsonify({"error": str(e)}), 401

    except Exception as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="webhooks_email",
            status="server_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="webhooks_email",
            status="error",
        )

        logger.error("Failed to process email webhook", error=str(e))
        return jsonify({"error": "Internal server error"}), 500
