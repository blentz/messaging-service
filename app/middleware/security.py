"""
Security middleware for webhook validation and request protection.
"""

import hashlib
import hmac
import time

from flask import current_app, request
from werkzeug.exceptions import BadRequest, Unauthorized

from app.utils.logging import get_logger, log_security_event
from app.utils.metrics import get_metrics_manager


def validate_webhook_signature(provider: str):
    """
    Validate webhook signature using HMAC-SHA256.

    Args:
        provider: Provider name ('twilio' or 'sendgrid')

    Raises:
        Unauthorized: If signature validation fails
    """
    logger = get_logger()
    metrics = get_metrics_manager()

    # Get the appropriate secret for the provider
    if provider == "twilio":
        secret = current_app.config.get("TWILIO_WEBHOOK_SECRET")
        signature_header = "X-Twilio-Signature"
    elif provider == "sendgrid":
        secret = current_app.config.get("SENDGRID_WEBHOOK_SECRET")
        signature_header = "X-SendGrid-Signature"
    else:
        log_security_event(
            "unknown_webhook_provider",
            severity="error",
            provider=provider,
            remote_addr=request.remote_addr,
        )
        unknown_provider_msg = "Unknown webhook provider"
        raise BadRequest(unknown_provider_msg)

    if not secret:
        log_security_event(
            "missing_webhook_secret", severity="error", provider=provider
        )
        webhook_secret_msg = "Webhook secret not configured"
        raise Unauthorized(webhook_secret_msg)

    # Get signature from headers
    provided_signature = request.headers.get(signature_header)
    if not provided_signature:
        log_security_event(
            "missing_webhook_signature",
            severity="warning",
            provider=provider,
            remote_addr=request.remote_addr,
        )
        metrics.increment_counter(
            "authentication_attempts_total",
            status="missing_signature",
            provider=provider,
        )
        missing_header_msg = f"Missing {signature_header} header"
        raise Unauthorized(missing_header_msg)

    # Get request data
    request_data = request.get_data()
    request_url = request.url

    # Calculate expected signature
    if provider == "twilio":
        # Twilio uses URL + POST data for signature
        signature_payload = request_url.encode() + request_data
    else:
        # SendGrid uses just the request body
        signature_payload = request_data

    expected_signature = hmac.new(
        secret.encode(), signature_payload, hashlib.sha256
    ).hexdigest()

    # For Twilio, signature is base64 encoded
    if provider == "twilio":
        import base64

        expected_signature = base64.b64encode(
            hmac.new(secret.encode(), signature_payload, hashlib.sha1).digest()
        ).decode()

    # Compare signatures (constant time comparison)
    if not hmac.compare_digest(provided_signature, expected_signature):
        log_security_event(
            "invalid_webhook_signature",
            severity="warning",
            provider=provider,
            provided_signature_prefix=provided_signature[:16] + "...",
            remote_addr=request.remote_addr,
        )
        metrics.increment_counter(
            "authentication_attempts_total",
            status="invalid_signature",
            provider=provider,
        )
        invalid_signature_msg = "Invalid webhook signature"
        raise Unauthorized(invalid_signature_msg)

    log_security_event(
        "webhook_signature_validated",
        provider=provider,
        remote_addr=request.remote_addr,
    )
    metrics.increment_counter(
        "authentication_attempts_total", status="success", provider=provider
    )


def validate_timestamp(max_age_seconds: int = 300):
    """
    Validate request timestamp to prevent replay attacks.

    Args:
        max_age_seconds: Maximum age of request in seconds (default 5 minutes)

    Raises:
        BadRequest: If timestamp is invalid or too old
    """
    timestamp_header = request.headers.get("X-Timestamp")
    if not timestamp_header:
        log_security_event(
            "missing_timestamp_header",
            severity="warning",
            remote_addr=request.remote_addr,
        )
        missing_timestamp_msg = "Missing X-Timestamp header"
        raise BadRequest(missing_timestamp_msg)

    try:
        request_time = int(timestamp_header)
        current_time = int(time.time())

        if abs(current_time - request_time) > max_age_seconds:
            log_security_event(
                "request_timestamp_too_old",
                severity="warning",
                request_time=request_time,
                current_time=current_time,
                age_seconds=abs(current_time - request_time),
                remote_addr=request.remote_addr,
            )
            timestamp_too_old_msg = "Request timestamp too old"
            raise BadRequest(timestamp_too_old_msg)

    except ValueError:
        log_security_event(
            "invalid_timestamp_format",
            severity="warning",
            timestamp=timestamp_header,
            remote_addr=request.remote_addr,
        )
        invalid_timestamp_msg = "Invalid timestamp format"
        raise BadRequest(invalid_timestamp_msg)


def validate_content_length(max_size_bytes: int = 10 * 1024 * 1024):
    """
    Validate request content length to prevent DoS attacks.

    Args:
        max_size_bytes: Maximum request size in bytes (default 10MB)

    Raises:
        BadRequest: If content is too large
    """
    content_length = request.content_length
    if content_length and content_length > max_size_bytes:
        log_security_event(
            "request_too_large",
            severity="warning",
            content_length=content_length,
            max_size=max_size_bytes,
            remote_addr=request.remote_addr,
        )
        request_too_large_msg = "Request too large"
        raise BadRequest(request_too_large_msg)


def validate_content_type(allowed_types: list = None):
    """
    Validate request content type.

    Args:
        allowed_types: List of allowed content types (default: application/json)

    Raises:
        BadRequest: If content type is not allowed
    """
    if allowed_types is None:
        allowed_types = ["application/json"]

    content_type = request.content_type
    if content_type not in allowed_types:
        log_security_event(
            "invalid_content_type",
            severity="warning",
            content_type=content_type,
            allowed_types=allowed_types,
            remote_addr=request.remote_addr,
        )
        invalid_content_type_msg = (
            f"Content type must be one of: {', '.join(allowed_types)}"
        )
        raise BadRequest(invalid_content_type_msg)


def sanitize_input(data: dict) -> dict:
    """
    Sanitize input data to prevent injection attacks.

    Args:
        data: Input data dictionary

    Returns:
        Sanitized data dictionary
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Basic XSS prevention - remove script tags and other dangerous HTML
            import re

            value = re.sub(
                r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL
            )
            value = re.sub(
                r"<iframe[^>]*>.*?</iframe>", "", value, flags=re.IGNORECASE | re.DOTALL
            )
            value = re.sub(r"javascript:", "", value, flags=re.IGNORECASE)

            # Limit string length
            if len(value) > 10000:
                log_security_event(
                    "input_string_too_long",
                    severity="warning",
                    field=key,
                    length=len(value),
                )
                value = value[:10000]

        elif isinstance(value, dict):
            value = sanitize_input(value)

        elif isinstance(value, list):
            value = [
                sanitize_input(item) if isinstance(item, dict) else item
                for item in value
            ]

        sanitized[key] = value

    return sanitized
