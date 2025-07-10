"""
Comprehensive unit tests for database utilities to achieve 100% coverage.
"""

import pytest
from unittest.mock import Mock, patch
from flask import Flask

from app.utils.database import init_db, reset_db, db


class TestDatabaseUtils:
    """Comprehensive test suite for database utilities."""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        return app

    @patch('app.utils.database.db.create_all')
    def test_init_db(self, mock_create_all, app):
        """Test init_db function calls db.create_all() within app context."""
        
        init_db(app)
        
        # Verify create_all was called
        mock_create_all.assert_called_once()

    @patch('app.utils.database.db.create_all')
    @patch('app.utils.database.db.drop_all')
    def test_reset_db(self, mock_drop_all, mock_create_all, app):
        """Test reset_db function calls db.drop_all() and db.create_all() within app context."""
        
        reset_db(app)
        
        # Verify both operations were called
        mock_drop_all.assert_called_once()
        mock_create_all.assert_called_once()

    def test_init_db_with_real_db(self, app):
        """Test init_db with real database operations."""
        # Initialize the db with the app
        db.init_app(app)
        
        # Test that init_db doesn't raise an exception
        try:
            init_db(app)
        except Exception as e:
            pytest.fail(f"init_db raised an exception: {e}")

    def test_reset_db_with_real_db(self, app):
        """Test reset_db with real database operations."""
        # Initialize the db with the app  
        db.init_app(app)
        
        # Test that reset_db doesn't raise an exception
        try:
            reset_db(app)
        except Exception as e:
            pytest.fail(f"reset_db raised an exception: {e}")