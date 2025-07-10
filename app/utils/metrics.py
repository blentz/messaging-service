"""
OpenTelemetry metrics setup for debugging and monitoring.
"""

from flask import Flask
from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource


class MetricsManager:
    """Manages OpenTelemetry metrics for the messaging service."""

    def __init__(self):
        self.meter = None
        self.counters: dict[str, metrics.Counter] = {}
        self.histograms: dict[str, metrics.Histogram] = {}
        self.gauges: dict[str, metrics.UpDownCounter] = {}

    def setup(self, app: Flask) -> None:
        """Set up OpenTelemetry metrics with Prometheus exporter."""
        if not app.config.get("OTEL_METRICS_ENABLED", True):
            return

        # Create resource
        resource = Resource.create(
            {"service.name": "messaging-service", "service.version": "0.1.0"}
        )

        # Set up Prometheus metric reader
        reader = PrometheusMetricReader()
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)

        # Get meter
        self.meter = metrics.get_meter("messaging-service")

        # Initialize metrics
        self._create_metrics()

    def _create_metrics(self) -> None:
        """Create all required metrics."""
        # Message processing metrics
        self.counters["messages_sent_total"] = self.meter.create_counter(
            name="messages_sent_total",
            description="Total messages sent by type",
            unit="1",
        )

        self.counters["messages_received_total"] = self.meter.create_counter(
            name="messages_received_total",
            description="Total messages received by type",
            unit="1",
        )

        self.histograms["message_processing_duration_seconds"] = (
            self.meter.create_histogram(
                name="message_processing_duration_seconds",
                description="Time to process messages",
                unit="s",
            )
        )

        self.histograms["provider_response_duration_seconds"] = (
            self.meter.create_histogram(
                name="provider_response_duration_seconds",
                description="Provider API response times",
                unit="s",
            )
        )

        self.counters["provider_errors_total"] = self.meter.create_counter(
            name="provider_errors_total",
            description="Provider errors by type and status code",
            unit="1",
        )

        # API endpoint metrics
        self.counters["http_requests_total"] = self.meter.create_counter(
            name="http_requests_total",
            description="HTTP requests by method, endpoint, status",
            unit="1",
        )

        self.histograms["http_request_duration_seconds"] = self.meter.create_histogram(
            name="http_request_duration_seconds",
            description="HTTP request processing time",
            unit="s",
        )

        self.histograms["webhook_processing_duration_seconds"] = (
            self.meter.create_histogram(
                name="webhook_processing_duration_seconds",
                description="Webhook processing time",
                unit="s",
            )
        )

        self.counters["authentication_attempts_total"] = self.meter.create_counter(
            name="authentication_attempts_total",
            description="Auth attempts by success/failure",
            unit="1",
        )

        # Database metrics
        self.counters["database_queries_total"] = self.meter.create_counter(
            name="database_queries_total",
            description="Database queries by operation type",
            unit="1",
        )

        self.histograms["database_query_duration_seconds"] = (
            self.meter.create_histogram(
                name="database_query_duration_seconds",
                description="Database query execution time",
                unit="s",
            )
        )

        self.counters["conversation_creation_total"] = self.meter.create_counter(
            name="conversation_creation_total",
            description="New conversations created",
            unit="1",
        )

        self.gauges["active_conversations_gauge"] = self.meter.create_up_down_counter(
            name="active_conversations_gauge",
            description="Current active conversations",
            unit="1",
        )

        # System health metrics
        self.gauges["application_up"] = self.meter.create_up_down_counter(
            name="application_up", description="Application health status", unit="1"
        )

        self.gauges["memory_usage_bytes"] = self.meter.create_up_down_counter(
            name="memory_usage_bytes", description="Memory usage", unit="byte"
        )

        self.gauges["active_connections_gauge"] = self.meter.create_up_down_counter(
            name="active_connections_gauge",
            description="Active database connections",
            unit="1",
        )

    def increment_counter(self, name: str, amount: int = 1, **attributes) -> None:
        """Increment a counter metric."""
        if name in self.counters:
            self.counters[name].add(amount, attributes)

    def record_histogram(self, name: str, value: float, **attributes) -> None:
        """Record a histogram value."""
        if name in self.histograms:
            self.histograms[name].record(value, attributes)

    def set_gauge(self, name: str, value: int, **attributes) -> None:
        """Set a gauge value."""
        if name in self.gauges:
            self.gauges[name].add(value, attributes)


# Global metrics manager instance
metrics_manager = MetricsManager()


def setup_metrics(app: Flask) -> None:
    """Set up metrics for the Flask application."""
    metrics_manager.setup(app)

    # Set application as healthy
    metrics_manager.set_gauge("application_up", 1)


def get_metrics_manager() -> MetricsManager:
    """Get the global metrics manager instance."""
    return metrics_manager
