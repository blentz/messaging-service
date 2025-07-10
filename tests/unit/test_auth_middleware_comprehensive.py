"""
Comprehensive unit tests for auth middleware to achieve 100% coverage.
"""

import pytest
from unittest.mock import Mock, patch
from flask import Flask, g

from app.middleware.auth import require_api_key, require_permission, get_current_user, get_current_api_key
from werkzeug.exceptions import Unauthorized


class TestAuthMiddleware:
    """Comprehensive test suite for auth middleware."""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config['AUTH_API_KEY_HEADER'] = 'X-API-Key'
        return app

    @patch('app.middleware.auth.log_security_event')
    @patch('app.middleware.auth.get_metrics_manager')
    @patch('app.middleware.auth.get_logger')
    def test_require_permission_no_current_user(self, mock_logger, mock_metrics, mock_log_event, app):
        """Test require_permission decorator when no current_user in g."""
        
        @require_permission("messages:send")
        def test_endpoint():
            return "success"
        
        with app.test_request_context():
            # Ensure g.current_user is not set
            if hasattr(g, 'current_user'):
                delattr(g, 'current_user')
            
            with pytest.raises(Unauthorized, match="Authentication required"):
                test_endpoint()

    @patch('app.middleware.auth.log_security_event')
    @patch('app.middleware.auth.get_metrics_manager')
    @patch('app.middleware.auth.get_logger')
    def test_require_permission_denied_with_logging(self, mock_logger, mock_metrics, mock_log_event, app):
        """Test require_permission decorator with permission denied and security logging."""
        
        @require_permission("admin:delete")
        def test_endpoint():
            return "success"
        
        with app.test_request_context():
            # Set up user with limited permissions
            g.current_user = {
                "user_id": "user_1",
                "permissions": ["messages:send", "conversations:read"]
            }
            
            with pytest.raises(Unauthorized, match="Permission required: admin:delete"):
                test_endpoint()
            
            # Verify security logging was called
            mock_log_event.assert_called_once_with(
                "permission_denied",
                severity="warning",
                user_id="user_1",
                required_permission="admin:delete",
                user_permissions=["messages:send", "conversations:read"],
                endpoint=None,
            )

    def test_get_current_user_when_set(self, app):
        """Test get_current_user when current_user is set in g."""
        with app.test_request_context():
            expected_user = {"user_id": "test_user", "permissions": ["test"]}
            g.current_user = expected_user
            
            result = get_current_user()
            assert result == expected_user

    def test_get_current_user_when_not_set(self, app):
        """Test get_current_user when current_user is not set in g."""
        with app.test_request_context():
            # Ensure g.current_user is not set
            if hasattr(g, 'current_user'):
                delattr(g, 'current_user')
            
            result = get_current_user()
            assert result is None

    def test_get_current_api_key_when_set(self, app):
        """Test get_current_api_key when api_key is set in g."""
        with app.test_request_context():
            expected_key = "api_key_123"
            g.api_key = expected_key
            
            result = get_current_api_key()
            assert result == expected_key

    def test_get_current_api_key_when_not_set(self, app):
        """Test get_current_api_key when api_key is not set in g."""
        with app.test_request_context():
            # Ensure g.api_key is not set
            if hasattr(g, 'api_key'):
                delattr(g, 'api_key')
            
            result = get_current_api_key()
            assert result is None

    @patch('app.middleware.auth.log_security_event')
    @patch('app.middleware.auth.get_metrics_manager')
    @patch('app.middleware.auth.get_logger')
    def test_require_permission_wildcard_access(self, mock_logger, mock_metrics, mock_log_event, app):
        """Test require_permission decorator with wildcard permission."""
        
        @require_permission("admin:delete")
        def test_endpoint():
            return "success"
        
        with app.test_request_context():
            # Set up user with wildcard permissions
            g.current_user = {
                "user_id": "admin",
                "permissions": ["*"]
            }
            
            result = test_endpoint()
            assert result == "success"
            
            # Verify no security logging for denied access
            mock_log_event.assert_not_called()

    @patch('app.middleware.auth.log_security_event')
    @patch('app.middleware.auth.get_metrics_manager')
    @patch('app.middleware.auth.get_logger')
    def test_require_permission_specific_access(self, mock_logger, mock_metrics, mock_log_event, app):
        """Test require_permission decorator with specific matching permission."""
        
        @require_permission("messages:send")
        def test_endpoint():
            return "success"
        
        with app.test_request_context():
            # Set up user with specific matching permission
            g.current_user = {
                "user_id": "user_1",
                "permissions": ["messages:send", "conversations:read"]
            }
            
            result = test_endpoint()
            assert result == "success"
            
            # Verify no security logging for denied access
            mock_log_event.assert_not_called()

    @patch('app.middleware.auth.log_security_event')
    @patch('app.middleware.auth.get_metrics_manager')
    @patch('app.middleware.auth.get_logger')
    def test_require_permission_no_permissions_list(self, mock_logger, mock_metrics, mock_log_event, app):
        """Test require_permission decorator when user has no permissions list."""
        
        @require_permission("messages:send")
        def test_endpoint():
            return "success"
        
        with app.test_request_context():
            # Set up user without permissions key
            g.current_user = {
                "user_id": "user_1"
                # No permissions key
            }
            
            with pytest.raises(Unauthorized, match="Permission required: messages:send"):
                test_endpoint()
            
            # Verify security logging was called with empty permissions
            mock_log_event.assert_called_once_with(
                "permission_denied",
                severity="warning",
                user_id="user_1",
                required_permission="messages:send",
                user_permissions=[],  # get() returns [] as default
                endpoint=None,
            )