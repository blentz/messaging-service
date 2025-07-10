"""
Flask application factory for unified messaging service.
"""

from flask import Flask
from opentelemetry.instrumentation.flask import FlaskInstrumentor

from app.api.conversations import conversations_bp
from app.api.messages import messages_bp
from app.api.webhooks import webhooks_bp
from app.config import Config
from app.utils.database import db
from app.utils.logging import setup_logging
from app.utils.metrics import setup_metrics


def create_app(config_class=Config):
    """Create Flask application using factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Setup observability
    setup_logging(app)
    setup_metrics(app)

    # Initialize OpenTelemetry instrumentation
    FlaskInstrumentor().instrument_app(app)

    # Register blueprints
    app.register_blueprint(messages_bp, url_prefix="/api")
    app.register_blueprint(webhooks_bp, url_prefix="/api")
    app.register_blueprint(conversations_bp, url_prefix="/api")

    # Health check endpoint
    @app.route("/health")
    def health_check():
        return {"status": "healthy", "service": "messaging-service"}

    return app
