"""
Database utilities and initialization.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Initialize database with application context."""
    with app.app_context():
        db.create_all()


def reset_db(app):
    """Reset database - useful for testing."""
    with app.app_context():
        db.drop_all()
        db.create_all()
