"""
Authentication middleware for API key validation.
"""

import functools

from flask import current_app, g, request
from werkzeug.exceptions import Unauthorized

from app.utils.logging import get_logger, log_security_event
from app.utils.metrics import get_metrics_manager

# Mock API keys for development/testing
VALID_API_KEYS = {
    "api_key_123": {
        "user_id": "user_1",
        "permissions": ["messages:send", "conversations:read"],
    },
    "api_key_456": {
        "user_id": "user_2",
        "permissions": ["messages:send", "messages:receive", "conversations:read"],
    },
    "admin_key_789": {"user_id": "admin", "permissions": ["*"]},
}


def require_api_key(f):
    """
    Decorator to require API key authentication for endpoints.

    Validates API key from X-API-Key header and sets g.current_user.
    """

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        logger = get_logger()
        metrics = get_metrics_manager()

        # Get API key from header
        api_key_header = current_app.config.get("AUTH_API_KEY_HEADER", "X-API-Key")
        api_key = request.headers.get(api_key_header)

        if not api_key:
            log_security_event(
                "missing_api_key",
                severity="warning",
                endpoint=request.endpoint,
                remote_addr=request.remote_addr,
            )
            metrics.increment_counter(
                "authentication_attempts_total",
                status="missing_key",
                endpoint=request.endpoint,
            )
            api_key_required_msg = "API key required"
            raise Unauthorized(api_key_required_msg)

        # Validate API key
        user_data = VALID_API_KEYS.get(api_key)
        if not user_data:
            log_security_event(
                "invalid_api_key",
                severity="warning",
                api_key_prefix=api_key[:8] + "...",
                endpoint=request.endpoint,
                remote_addr=request.remote_addr,
            )
            metrics.increment_counter(
                "authentication_attempts_total",
                status="invalid_key",
                endpoint=request.endpoint,
            )
            invalid_api_key_msg = "Invalid API key"
            raise Unauthorized(invalid_api_key_msg)

        # Set current user in request context
        g.current_user = user_data
        g.api_key = api_key

        log_security_event(
            "successful_authentication",
            user_id=user_data["user_id"],
            endpoint=request.endpoint,
        )
        metrics.increment_counter(
            "authentication_attempts_total", status="success", endpoint=request.endpoint
        )

        return f(*args, **kwargs)

    return decorated_function


def require_permission(permission: str):
    """
    Decorator to require specific permission for endpoints.

    Args:
        permission: Required permission string (e.g., "messages:send")
    """

    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, "current_user"):
                auth_required_msg = "Authentication required"
                raise Unauthorized(auth_required_msg)

            user_permissions = g.current_user.get("permissions", [])

            # Check for wildcard permission or specific permission
            if "*" not in user_permissions and permission not in user_permissions:
                log_security_event(
                    "permission_denied",
                    severity="warning",
                    user_id=g.current_user.get("user_id"),
                    required_permission=permission,
                    user_permissions=user_permissions,
                    endpoint=request.endpoint,
                )
                permission_required_msg = f"Permission required: {permission}"
                raise Unauthorized(permission_required_msg)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_current_user():
    """Get current authenticated user from request context."""
    return getattr(g, "current_user", None)


def get_current_api_key():
    """Get current API key from request context."""
    return getattr(g, "api_key", None)
