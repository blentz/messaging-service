"""
Provider model for managing mock provider configurations.
"""

from enum import Enum

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import ENUM, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.utils.database import db


class ProviderType(Enum):
    """Enum for provider types."""

    SMS_MMS = "sms_mms"
    EMAIL = "email"


class Provider(db.Model):
    """
    Provider model for managing mock provider configurations.

    Stores configuration for Twilio and SendGrid mock providers,
    including error simulation settings for testing.
    """

    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    provider_type: Mapped[ProviderType] = mapped_column(
        ENUM(ProviderType), nullable=False
    )
    config: Mapped[dict] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_simulation: Mapped[dict] = mapped_column(JSON, nullable=True)

    def __repr__(self):
        return f"<Provider {self.name}: {self.provider_type.value}>"

    @classmethod
    def get_by_name(cls, name):
        """Get provider by name."""
        return cls.query.filter_by(name=name).first()

    @classmethod
    def get_active_providers(cls, provider_type=None):
        """Get all active providers, optionally filtered by type."""
        query = cls.query.filter_by(is_active=True)
        if provider_type:
            query = query.filter_by(provider_type=provider_type)
        return query.all()

    def to_dict(self):
        """Convert provider to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type.value,
            "config": self.config,
            "is_active": self.is_active,
            "error_simulation": self.error_simulation,
        }
