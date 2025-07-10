# Unified Messaging Service Documentation

Welcome to the Unified Messaging Service documentation. This service provides a unified API for sending and receiving SMS, MMS, and Email messages with automatic conversation management.

## Quick Start

1. **Start the database**: `make db-up`
2. **Start the service**: `make run` (or `./bin/start.sh`)
3. **Test the service**: `make test` (or `./bin/test.sh`)

The service will be available at `http://localhost:8080`

## Documentation Index

### Getting Started
- [Installation & Setup](installation.md) - How to install and configure the service
- [Quick Start Guide](quickstart.md) - Get up and running in 5 minutes
- [Configuration](configuration.md) - Environment variables and settings

### API Reference
- [API Overview](api/overview.md) - Introduction to the messaging API
- [Message Endpoints](api/messages.md) - Sending SMS, MMS, and Email messages
- [Webhook Endpoints](api/webhooks.md) - Receiving inbound messages
- [Conversation Endpoints](api/conversations.md) - Managing conversations
- [Authentication](api/authentication.md) - API key authentication
- [Error Handling](api/errors.md) - Error codes and responses

### Features
- [Conversation Management](features/conversations.md) - How messages are grouped into conversations
- [Provider Integration](features/providers.md) - SMS/MMS and Email provider handling
- [Security](features/security.md) - Authentication and webhook security
- [Observability](features/observability.md) - Logging and metrics

### Development
- [Architecture](development/architecture.md) - System design and components
- [Database Schema](development/database.md) - Data models and relationships
- [Testing](development/testing.md) - Running tests and coverage
- [Contributing](development/contributing.md) - Development workflow

### Operations
- [Deployment](operations/deployment.md) - Production deployment guide
- [Monitoring](operations/monitoring.md) - Metrics and alerting
- [Troubleshooting](operations/troubleshooting.md) - Common issues and solutions
- [Maintenance](operations/maintenance.md) - Backup and maintenance tasks

## Support

For questions or issues:
- Check the [Troubleshooting Guide](operations/troubleshooting.md)
- Review the [API Documentation](api/overview.md)
- Check the logs for error details

## Version

This documentation is for Unified Messaging Service v0.1.0