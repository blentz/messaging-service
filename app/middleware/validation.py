"""
Input validation middleware for API requests.
"""

import re

from werkzeug.exceptions import BadRequest

from app.utils.logging import get_logger, log_security_event


def validate_sms_message_request(data: dict) -> dict:
    """
    Validate SMS/MMS message request data.

    Args:
        data: Request data dictionary

    Returns:
        Validated and normalized data

    Raises:
        BadRequest: If validation fails
    """
    logger = get_logger()

    # Required fields
    required_fields = ["from", "to", "type", "body"]
    for field in required_fields:
        if field not in data:
            error_msg = f"Missing required field: {field}"
            raise BadRequest(error_msg)

    # Validate phone numbers (E.164 format)
    phone_pattern = r"^\+[1-9]\d{1,14}$"

    if not re.match(phone_pattern, data["from"]):
        log_security_event(
            "invalid_phone_number_format",
            field="from",
            value=data["from"][:5] + "...",
            expected_format="E.164",
        )
        error_msg = "Invalid 'from' phone number format. Must be E.164 format."
        raise BadRequest(error_msg)

    if not re.match(phone_pattern, data["to"]):
        log_security_event(
            "invalid_phone_number_format",
            field="to",
            value=data["to"][:5] + "...",
            expected_format="E.164",
        )
        error_msg = "Invalid 'to' phone number format. Must be E.164 format."
        raise BadRequest(error_msg)

    # Validate message type
    if data["type"].lower() not in ["sms", "mms"]:
        error_msg = "Message type must be 'sms' or 'mms'"
        raise BadRequest(error_msg)

    # Validate body
    if not data["body"] or len(data["body"]) > 1600:
        error_msg = "Message body must be between 1 and 1600 characters"
        raise BadRequest(error_msg)

    # Validate attachments for MMS
    if data["type"].lower() == "mms":
        attachments = data.get("attachments", [])
        if attachments:
            if len(attachments) > 10:
                error_msg = "MMS messages cannot have more than 10 attachments"
                raise BadRequest(error_msg)

            for url in attachments:
                if not _is_valid_url(url):
                    error_msg = f"Invalid attachment URL: {url}"
                    raise BadRequest(error_msg)

    # Validate timestamp if provided
    if data.get("timestamp"):
        if not _is_valid_iso_timestamp(data["timestamp"]):
            error_msg = "Invalid timestamp format. Must be ISO 8601."
            raise BadRequest(error_msg)

    return data


def validate_email_message_request(data: dict) -> dict:
    """
    Validate email message request data.

    Args:
        data: Request data dictionary

    Returns:
        Validated and normalized data

    Raises:
        BadRequest: If validation fails
    """
    logger = get_logger()

    # Required fields
    required_fields = ["from", "to", "body"]
    for field in required_fields:
        if field not in data:
            error_msg = f"Missing required field: {field}"
            raise BadRequest(error_msg)

    # Validate email addresses
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, data["from"]):
        log_security_event(
            "invalid_email_format",
            field="from",
            value=data["from"],
        )
        error_msg = "Invalid 'from' email address format"
        raise BadRequest(error_msg)

    if not re.match(email_pattern, data["to"]):
        log_security_event("invalid_email_format", field="to", value=data["to"])
        error_msg = "Invalid 'to' email address format"
        raise BadRequest(error_msg)

    # Validate body
    if not data["body"]:
        error_msg = "Message body cannot be empty"
        raise BadRequest(error_msg)

    if len(data["body"]) > 1024 * 1024:  # 1MB limit
        error_msg = "Message body exceeds maximum size limit"
        raise BadRequest(error_msg)

    # Validate attachments
    attachments = data.get("attachments", [])
    if attachments:
        if len(attachments) > 25:
            error_msg = "Email messages cannot have more than 25 attachments"
            raise BadRequest(error_msg)

        for url in attachments:
            if not _is_valid_url(url):
                error_msg = f"Invalid attachment URL: {url}"
                raise BadRequest(error_msg)

    # Validate timestamp if provided
    if data.get("timestamp"):
        if not _is_valid_iso_timestamp(data["timestamp"]):
            error_msg = "Invalid timestamp format. Must be ISO 8601."
            raise BadRequest(error_msg)

    return data


def validate_sms_webhook_request(data: dict) -> dict:
    """
    Validate SMS/MMS webhook request data.

    Args:
        data: Webhook data dictionary

    Returns:
        Validated data

    Raises:
        BadRequest: If validation fails
    """
    # Required fields for SMS webhook
    required_fields = ["from", "to", "type", "messaging_provider_id", "body"]
    for field in required_fields:
        if field not in data:
            error_msg = f"Missing required field: {field}"
            raise BadRequest(error_msg)

    # Validate phone numbers
    phone_pattern = r"^\+[1-9]\d{1,14}$"

    if not re.match(phone_pattern, data["from"]):
        error_msg = "Invalid 'from' phone number format"
        raise BadRequest(error_msg)

    if not re.match(phone_pattern, data["to"]):
        error_msg = "Invalid 'to' phone number format"
        raise BadRequest(error_msg)

    # Validate message type
    if data["type"].lower() not in ["sms", "mms"]:
        error_msg = "Message type must be 'sms' or 'mms'"
        raise BadRequest(error_msg)

    # Validate provider ID
    if not data["messaging_provider_id"]:
        error_msg = "messaging_provider_id cannot be empty"
        raise BadRequest(error_msg)

    return data


def validate_email_webhook_request(data: dict) -> dict:
    """
    Validate email webhook request data.

    Args:
        data: Webhook data dictionary

    Returns:
        Validated data

    Raises:
        BadRequest: If validation fails
    """
    # Required fields for email webhook
    required_fields = ["from", "to", "xillio_id", "body"]
    for field in required_fields:
        if field not in data:
            error_msg = f"Missing required field: {field}"
            raise BadRequest(error_msg)

    # Validate email addresses
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, data["from"]):
        error_msg = "Invalid 'from' email address format"
        raise BadRequest(error_msg)

    if not re.match(email_pattern, data["to"]):
        error_msg = "Invalid 'to' email address format"
        raise BadRequest(error_msg)

    # Validate provider ID
    if not data["xillio_id"]:
        error_msg = "xillio_id cannot be empty"
        raise BadRequest(error_msg)

    return data


def validate_pagination_params(
    limit: int | None = None, offset: int | None = None
) -> tuple:
    """
    Validate pagination parameters.

    Args:
        limit: Maximum number of items to return
        offset: Number of items to skip

    Returns:
        Tuple of (validated_limit, validated_offset)

    Raises:
        BadRequest: If parameters are invalid
    """
    # Default values
    if limit is None:
        limit = 50
    if offset is None:
        offset = 0

    # Validate limit
    try:
        limit = int(limit)
        if limit < 1 or limit > 1000:
            error_msg = "Limit must be between 1 and 1000"
            raise BadRequest(error_msg)
    except (ValueError, TypeError):
        error_msg = "Limit must be a valid integer"
        raise BadRequest(error_msg)

    # Validate offset
    try:
        offset = int(offset)
        if offset < 0:
            error_msg = "Offset must be non-negative"
            raise BadRequest(error_msg)
    except (ValueError, TypeError):
        error_msg = "Offset must be a valid integer"
        raise BadRequest(error_msg)

    return limit, offset


def _is_valid_url(url: str) -> bool:
    """Check if URL is valid format."""
    url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(url_pattern, url))


def _is_valid_iso_timestamp(timestamp: str) -> bool:
    """Check if timestamp is valid ISO 8601 format."""
    try:
        from datetime import datetime

        # Try parsing with different ISO formats
        for fmt in [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S%z",
        ]:
            try:
                datetime.strptime(timestamp, fmt)
                return True
            except ValueError:
                continue
        return False
    except Exception:
        return False
