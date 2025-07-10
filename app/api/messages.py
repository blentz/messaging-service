"""
API endpoints for sending messages (SMS/MMS and Email).
"""

import time

from flask import Blueprint, jsonify, request

from app.middleware.auth import require_api_key, require_permission
from app.providers.base import ProviderError
from app.middleware.security import (
    sanitize_input,
    validate_content_length,
    validate_content_type,
)
from app.middleware.validation import (
    validate_email_message_request,
    validate_sms_message_request,
)
from app.services.message_service import MessageService
from app.utils.logging import get_logger
from app.utils.metrics import get_metrics_manager

messages_bp = Blueprint("messages", __name__)
logger = get_logger()
metrics = get_metrics_manager()


@messages_bp.route("/messages/sms", methods=["POST"])
@require_api_key
@require_permission("messages:send")
def send_sms_message():
    """
    Send SMS/MMS message.

    POST /api/messages/sms

    Request body:
    {
        "from": "+18045551234",
        "to": "+12016661234",
        "type": "sms" | "mms",
        "body": "text message",
        "attachments": ["attachment-url"] | [] | null,
        "timestamp": "2024-11-01T14:00:00Z"
    }

    Response:
    {
        "message_id": 123,
        "status": "sent",
        "conversation_id": 456,
        "sent_at": "2024-11-01T14:00:00Z"
    }
    """
    start_time = time.time()

    try:
        # Validate request
        validate_content_type(["application/json"])
        validate_content_length()

        # Get and sanitize request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400

        data = sanitize_input(data)
        data = validate_sms_message_request(data)

        # Send message
        message_service = MessageService()
        result = message_service.send_sms_message(
            from_address=data["from"],
            to_address=data["to"],
            message_type=data["type"],
            body=data["body"],
            attachments=data.get("attachments"),
            timestamp=data.get("timestamp"),
        )

        # Track metrics
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="messages_sms",
            status="success",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="messages_sms",
        )

        logger.info(
            "SMS message sent successfully",
            message_id=result["message_id"],
            conversation_id=result["conversation_id"],
            message_type=data["type"],
        )

        return jsonify(result), 200

    except ValueError as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="messages_sms",
            status="validation_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="messages_sms",
            status="error",
        )

        logger.warning("SMS message validation failed", error=str(e))
        return jsonify({"error": str(e)}), 400

    except ProviderError as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="messages_sms",
            status="provider_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="messages_sms",
            status="error",
        )

        logger.warning("SMS message provider error", error=str(e))
        return jsonify({"error": str(e)}), e.status_code

    except Exception as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="messages_sms",
            status="server_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="messages_sms",
            status="error",
        )

        logger.error("Failed to send SMS message", error=str(e))
        return jsonify({"error": "Internal server error"}), 500


@messages_bp.route("/messages/email", methods=["POST"])
@require_api_key
@require_permission("messages:send")
def send_email_message():
    """
    Send email message.

    POST /api/messages/email

    Request body:
    {
        "from": "user@usehatchapp.com",
        "to": "contact@gmail.com",
        "body": "text message with or without html",
        "attachments": ["attachment-url"] | [],
        "timestamp": "2024-11-01T14:00:00Z"
    }

    Response:
    {
        "message_id": 123,
        "status": "sent",
        "conversation_id": 456,
        "sent_at": "2024-11-01T14:00:00Z"
    }
    """
    start_time = time.time()

    try:
        # Validate request
        validate_content_type(["application/json"])
        validate_content_length()

        # Get and sanitize request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400

        data = sanitize_input(data)
        data = validate_email_message_request(data)

        # Send message
        message_service = MessageService()
        result = message_service.send_email_message(
            from_address=data["from"],
            to_address=data["to"],
            body=data["body"],
            attachments=data.get("attachments"),
            timestamp=data.get("timestamp"),
        )

        # Track metrics
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="messages_email",
            status="success",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="messages_email",
        )

        logger.info(
            "Email message sent successfully",
            message_id=result["message_id"],
            conversation_id=result["conversation_id"],
        )

        return jsonify(result), 200

    except ValueError as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="messages_email",
            status="validation_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="messages_email",
            status="error",
        )

        logger.warning("Email message validation failed", error=str(e))
        return jsonify({"error": str(e)}), 400

    except ProviderError as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="messages_email",
            status="provider_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="messages_email",
            status="error",
        )

        logger.warning("Email message provider error", error=str(e))
        return jsonify({"error": str(e)}), e.status_code

    except Exception as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="POST",
            endpoint="messages_email",
            status="server_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="POST",
            endpoint="messages_email",
            status="error",
        )

        logger.error("Failed to send email message", error=str(e))
        return jsonify({"error": "Internal server error"}), 500
