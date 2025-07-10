"""
API endpoints for conversation management.
"""

import time

from flask import Blueprint, jsonify, request

from app.middleware.auth import require_api_key, require_permission
from app.middleware.validation import validate_pagination_params
from app.services.conversation_service import ConversationService
from app.utils.logging import get_logger
from app.utils.metrics import get_metrics_manager

conversations_bp = Blueprint("conversations", __name__)
logger = get_logger()
metrics = get_metrics_manager()


@conversations_bp.route("/conversations", methods=["GET"])
@require_api_key
@require_permission("conversations:read")
def get_conversations():
    """
    Get conversations list with pagination and optional search.

    GET /api/conversations?limit=50&offset=0&search=search_term

    Query parameters:
    - limit: Maximum number of conversations to return (default: 50, max: 1000)
    - offset: Number of conversations to skip (default: 0)
    - search: Optional search term for participant filtering

    Response:
    {
        "conversations": [
            {
                "id": 123,
                "participants": ["+18045551234", "+12016661234"],
                "conversation_type": "sms_mms",
                "created_at": "2024-11-01T14:00:00Z",
                "updated_at": "2024-11-01T15:00:00Z",
                "last_message_at": "2024-11-01T15:00:00Z",
                "message_count": 5,
                "metadata": {}
            }
        ],
        "total": 100,
        "limit": 50,
        "offset": 0
    }
    """
    start_time = time.time()

    try:
        # Get and validate query parameters
        limit = request.args.get("limit", 50)
        offset = request.args.get("offset", 0)
        search = request.args.get("search")

        limit, offset = validate_pagination_params(limit, offset)

        # Get conversations
        conversation_service = ConversationService()
        conversations, total = conversation_service.get_conversations(
            limit=limit, offset=offset, search=search
        )

        # Convert to response format
        conversation_list = [conv.to_dict() for conv in conversations]

        response = {
            "conversations": conversation_list,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

        # Track metrics
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="GET",
            endpoint="conversations",
            status="success",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="GET",
            endpoint="conversations",
        )

        logger.info(
            "Conversations retrieved successfully",
            total=total,
            returned=len(conversation_list),
            limit=limit,
            offset=offset,
            search=bool(search),
        )

        return jsonify(response), 200

    except ValueError as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="GET",
            endpoint="conversations",
            status="validation_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="GET",
            endpoint="conversations",
            status="error",
        )

        logger.warning("Conversations request validation failed", error=str(e))
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="GET",
            endpoint="conversations",
            status="server_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="GET",
            endpoint="conversations",
            status="error",
        )

        logger.error("Failed to retrieve conversations", error=str(e))
        return jsonify({"error": "Internal server error"}), 500


@conversations_bp.route(
    "/conversations/<int:conversation_id>/messages", methods=["GET"]
)
@require_api_key
@require_permission("conversations:read")
def get_conversation_messages(conversation_id):
    """
    Get messages for a specific conversation.

    GET /api/conversations/123/messages?limit=50&offset=0&since=2024-11-01T14:00:00Z

    Query parameters:
    - limit: Maximum number of messages to return (default: 50, max: 1000)
    - offset: Number of messages to skip (default: 0)
    - since: ISO timestamp to filter messages after (optional)

    Response:
    {
        "messages": [
            {
                "id": 456,
                "conversation_id": 123,
                "from": "+18045551234",
                "to": "+12016661234",
                "type": "sms",
                "direction": "outbound",
                "body": "Hello world",
                "attachments": [],
                "provider_id": "twilio_123",
                "provider_name": "twilio_mock",
                "status": "sent",
                "created_at": "2024-11-01T14:00:00Z",
                "updated_at": "2024-11-01T14:00:00Z",
                "sent_at": "2024-11-01T14:00:00Z"
            }
        ],
        "total": 10,
        "limit": 50,
        "offset": 0,
        "conversation_id": 123
    }
    """
    start_time = time.time()

    try:
        # Get and validate query parameters
        limit = request.args.get("limit", 50)
        offset = request.args.get("offset", 0)
        since = request.args.get("since")

        limit, offset = validate_pagination_params(limit, offset)

        # Get messages
        conversation_service = ConversationService()
        messages, total = conversation_service.get_conversation_messages(
            conversation_id=conversation_id, limit=limit, offset=offset, since=since
        )

        # Convert to response format
        message_list = [msg.to_dict() for msg in messages]

        response = {
            "messages": message_list,
            "total": total,
            "limit": limit,
            "offset": offset,
            "conversation_id": conversation_id,
        }

        # Track metrics
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="GET",
            endpoint="conversation_messages",
            status="success",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="GET",
            endpoint="conversation_messages",
        )

        logger.info(
            "Conversation messages retrieved successfully",
            conversation_id=conversation_id,
            total=total,
            returned=len(message_list),
            limit=limit,
            offset=offset,
            since=bool(since),
        )

        return jsonify(response), 200

    except ValueError as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="GET",
            endpoint="conversation_messages",
            status="validation_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="GET",
            endpoint="conversation_messages",
            status="error",
        )

        logger.warning(
            "Conversation messages request validation failed",
            conversation_id=conversation_id,
            error=str(e),
        )
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        duration = time.time() - start_time
        metrics.increment_counter(
            "http_requests_total",
            method="GET",
            endpoint="conversation_messages",
            status="server_error",
        )
        metrics.record_histogram(
            "http_request_duration_seconds",
            duration,
            method="GET",
            endpoint="conversation_messages",
            status="error",
        )

        logger.error(
            "Failed to retrieve conversation messages",
            conversation_id=conversation_id,
            error=str(e),
        )
        return jsonify({"error": "Internal server error"}), 500
