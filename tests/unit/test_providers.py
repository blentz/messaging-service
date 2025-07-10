"""
Unit tests for provider models and classes.
"""

import pytest
from unittest.mock import Mock, patch

from app.models.provider import Provider, ProviderType
from app.providers.base import MockProviderBase
from app.providers.twilio_mock import TwilioMockProvider
from app.providers.sendgrid_mock import SendGridMockProvider


class TestProviderModel:
    """Test Provider model."""

    def test_provider_creation(self, db_session):
        """Test creating a provider."""
        provider = Provider(
            name="test_provider",
            provider_type=ProviderType.SMS_MMS,
            is_active=True,
            config={"api_key": "test_key"}
        )
        db_session.add(provider)
        db_session.commit()
        
        assert provider.id is not None
        assert provider.name == "test_provider"
        assert provider.provider_type == ProviderType.SMS_MMS
        assert provider.is_active is True

    def test_get_by_name(self, db_session):
        """Test getting provider by name."""
        provider = Provider(
            name="test_provider",
            provider_type=ProviderType.SMS_MMS, 
            is_active=True,
            config={}
        )
        db_session.add(provider)
        db_session.commit()
        
        result = Provider.get_by_name("test_provider")
        assert result.name == "test_provider"

    def test_get_by_name_not_found(self, db_session):
        """Test getting provider by name when not found."""
        result = Provider.get_by_name("nonexistent")
        assert result is None

    def test_get_active_providers(self, db_session):
        """Test getting active providers."""
        active_provider = Provider(
            name="active",
            provider_type=ProviderType.SMS_MMS,
            is_active=True,
            config={}
        )
        inactive_provider = Provider(
            name="inactive", 
            provider_type=ProviderType.SMS_MMS,
            is_active=False,
            config={}
        )
        db_session.add_all([active_provider, inactive_provider])
        db_session.commit()
        
        result = Provider.get_active_providers(ProviderType.SMS_MMS)
        assert len(result) >= 1
        provider_names = [p.name for p in result]
        assert "active" in provider_names
        assert "inactive" not in provider_names

    def test_to_dict(self, db_session):
        """Test provider to_dict method."""
        provider = Provider(
            name="test_provider",
            provider_type=ProviderType.SMS_MMS,
            is_active=True,
            config={"key": "value"}
        )
        db_session.add(provider)
        db_session.commit()
        
        result = provider.to_dict()
        assert result["name"] == "test_provider"
        assert result["provider_type"] == "sms_mms"
        assert result["is_active"] is True
        assert result["config"] == {"key": "value"}


class TestMockProviderBase:
    """Test mock provider base class."""

    def test_initialization(self):
        """Test mock provider initialization."""
        # Create concrete implementation
        class TestProvider(MockProviderBase):
            def send_message(self, message_data):
                return {"id": "test", "status": "sent"}
            
            def validate_request(self, message_data):
                return True
            
            def health_check(self):
                return {"status": "healthy"}
        
        provider = TestProvider("test_provider")
        assert provider.provider_name == "test_provider"
        assert provider.error_simulation_config["error_rate"] == 0.0

    def test_send_message_implementation(self):
        """Test send_message implementation requirement."""
        class TestProvider(MockProviderBase):
            def send_message(self, message_data):
                return {"id": "test", "status": "sent"}
            
            def validate_request(self, message_data):
                return True
            
            def health_check(self):
                return {"status": "healthy"}
        
        provider = TestProvider("test")
        result = provider.send_message({"test": "data"})
        assert result["status"] == "sent"

    def test_health_check_implementation(self):
        """Test health_check implementation requirement."""
        class TestProvider(MockProviderBase):
            def send_message(self, message_data):
                return {"id": "test", "status": "sent"}
            
            def validate_request(self, message_data):
                return True
            
            def health_check(self):
                return {"status": "healthy"}
        
        provider = TestProvider("test")
        result = provider.health_check()
        assert result["status"] == "healthy"


class TestTwilioMockProvider:
    """Test Twilio mock provider."""

    def test_initialization(self):
        """Test Twilio provider initialization."""
        provider = TwilioMockProvider()
        assert provider.provider_name == "twilio_mock"

    def test_send_message(self):
        """Test Twilio send message."""
        provider = TwilioMockProvider()
        message_data = {
            "from": "+12345678901",
            "to": "+19876543210", 
            "body": "Test message"
        }
        
        result = provider.send_message(message_data)
        assert result["sid"].startswith("SM")
        assert result["status"] == "sent"
        assert result["from"] == "+12345678901"
        assert result["to"] == "+19876543210"

    def test_health_check(self):
        """Test Twilio health check."""
        provider = TwilioMockProvider()
        result = provider.health_check()
        assert result["status"] == "healthy"
        assert result["provider"] == "twilio_mock"


class TestSendGridMockProvider:
    """Test SendGrid mock provider."""

    def test_initialization(self):
        """Test SendGrid provider initialization."""
        provider = SendGridMockProvider()
        assert provider.provider_name == "sendgrid_mock"

    def test_send_message(self):
        """Test SendGrid send message."""
        provider = SendGridMockProvider()
        message_data = {
            "from": "test@example.com",
            "to": "recipient@example.com",
            "body": "Test email"
        }
        
        result = provider.send_message(message_data)
        assert result["message_id"].startswith("sg_sendgrid_mock_")
        assert result["status"] == "accepted"
        assert result["from"] == "test@example.com"
        assert result["to"] == "recipient@example.com"

    def test_health_check(self):
        """Test SendGrid health check."""
        provider = SendGridMockProvider()
        result = provider.health_check()
        assert result["status"] == "healthy"
        assert result["provider"] == "sendgrid_mock"