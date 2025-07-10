"""
Structured logging setup for the messaging service.
"""

import logging
import sys
from typing import Any

import structlog
from flask import Flask, g, request


def setup_logging(app: Flask) -> None:
    """
    Set up structured logging with JSON format.

    Configures structlog for JSON output with standard fields:
    - timestamp, level, service, endpoint, user_id, conversation_id, message_id
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, app.config.get("LOG_LEVEL", "INFO"))
        ),
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=False,
    )

    # Set up Flask app logging
    app.logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    app.logger.addHandler(handler)
    app.logger.setLevel(getattr(logging, app.config.get("LOG_LEVEL", "INFO")))

    # Add request context processor
    @app.before_request
    def add_request_context():
        """Add request context to logging."""
        g.logger = structlog.get_logger().bind(
            service="messaging-service",
            endpoint=request.endpoint,
            method=request.method,
            path=request.path,
            remote_addr=request.remote_addr,
        )


def get_logger(**context: Any) -> structlog.BoundLogger:
    """
    Get a structured logger with optional context.

    Args:
        **context: Additional context to bind to the logger

    Returns:
        Bound logger with context
    """
    logger = structlog.get_logger()
    try:
        if hasattr(g, "logger"):
            logger = g.logger
    except RuntimeError:
        # Outside application context, use basic logger
        pass
    return logger.bind(**context)


def log_message_event(
    event: str, message_id: int = None, conversation_id: int = None, **context: Any
) -> None:
    """
    Log message-related events with standard context.

    Args:
        event: Event description
        message_id: Message ID for context
        conversation_id: Conversation ID for context
        **context: Additional context
    """
    logger_context = {}
    if message_id:
        logger_context["message_id"] = message_id
    if conversation_id:
        logger_context["conversation_id"] = conversation_id
    logger_context.update(context)

    get_logger(**logger_context).info(event)


def log_security_event(event: str, severity: str = "info", **context: Any) -> None:
    """
    Log security-related events.

    Args:
        event: Security event description
        severity: Event severity (info, warning, error)
        **context: Additional context
    """
    logger = get_logger(event_type="security", **context)
    getattr(logger, severity)(event)


def log_provider_event(event: str, provider_name: str, **context: Any) -> None:
    """
    Log provider-related events.

    Args:
        event: Provider event description
        provider_name: Name of the provider
        **context: Additional context
    """
    get_logger(provider_name=provider_name, **context).info(event)
