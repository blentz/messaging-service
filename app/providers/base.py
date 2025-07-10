"""
Base class for mock provider implementations.
"""

import random
import time
from abc import ABC, abstractmethod
from uuid import uuid4

from app.utils.logging import get_logger


class MockProviderBase(ABC):
    """Base class for all mock provider implementations."""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.logger = get_logger()
        self.error_simulation_config = {
            "error_rate": 0.0,  # 0-1 probability of errors
            "rate_limit_rate": 0.0,  # 0-1 probability of rate limits
            "timeout_rate": 0.0,  # 0-1 probability of timeouts
            "server_error_rate": 0.0,  # 0-1 probability of server errors
        }

    @abstractmethod
    def send_message(self, message_data: dict) -> dict:
        """Send message through the provider. Must be implemented by subclasses."""

    @abstractmethod
    def validate_request(self, message_data: dict) -> bool:
        """Validate request against provider schema. Must be implemented by subclasses."""

    def health_check(self) -> dict:
        """
        Check provider health status.
        
        Returns:
            Dict with health status information
        """
        return {
            "status": "healthy",
            "provider": self.provider_name,
            "timestamp": time.time()
        }

    def simulate_errors(self) -> None:
        """Simulate various provider errors for testing."""
        config = self.error_simulation_config

        # Simulate timeout
        if random.random() < config["timeout_rate"]:
            time.sleep(30)  # Simulate timeout
            timeout_msg = "Provider request timed out"
            raise TimeoutError(timeout_msg)

        # Simulate rate limiting
        if random.random() < config["rate_limit_rate"]:
            rate_limit_msg = "Rate limit exceeded"
            raise ProviderRateLimitError(rate_limit_msg, status_code=429)

        # Simulate server errors
        if random.random() < config["server_error_rate"]:
            server_error_msg = "Internal server error"
            raise ProviderServerError(server_error_msg, status_code=500)

        # Simulate general errors
        if random.random() < config["error_rate"]:
            provider_error_msg = "Provider error occurred"
            raise ProviderError(provider_error_msg, status_code=400)

    def generate_mock_id(self) -> str:
        """Generate a mock provider ID."""
        return f"{self.provider_name}_{uuid4().hex[:12]}"

    def configure_error_simulation(self, config: dict) -> None:
        """Configure error simulation rates."""
        self.error_simulation_config.update(config)


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class ProviderRateLimitError(ProviderError):
    """Exception for rate limit errors."""

    def __init__(self, message: str, status_code: int = 429):
        super().__init__(message, status_code)


class ProviderServerError(ProviderError):
    """Exception for server errors."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)
