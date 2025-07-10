# Quick Start Guide

Get the Unified Messaging Service running in 5 minutes.

## Prerequisites

- Python 3.11+
- Docker or Podman for database
- uv package manager

## 1. Clone and Setup

```bash
git clone <repository-url>
cd messaging-service
make setup
```

## 2. Start Database

```bash
make db-up
```

This starts a PostgreSQL 15 database container with:
- Database: `messaging_service`
- User: `messaging_user` 
- Password: `messaging_password`
- Port: `5432`

## 3. Start the Service

```bash
make run
```

Or directly:
```bash
./bin/start.sh
```

The service starts on `http://localhost:8080`

## 4. Test the Service

```bash
make test
```

Or directly:
```bash
./bin/test.sh
```

## 5. Send Your First Message

### Send an SMS

```bash
curl -X POST http://localhost:8080/api/messages/sms \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin_key_789" \
  -d '{
    "from": "+12016661234",
    "to": "+18045551234",
    "type": "sms",
    "body": "Hello! This is a test SMS message.",
    "attachments": null,
    "timestamp": "2024-11-01T14:00:00Z"
  }'
```

### Send an Email

```bash
curl -X POST http://localhost:8080/api/messages/email \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin_key_789" \
  -d '{
    "from": "user@usehatchapp.com",
    "to": "contact@gmail.com",
    "body": "Hello! This is a test email message.",
    "attachments": [],
    "timestamp": "2024-11-01T14:00:00Z"
  }'
```

### Get Conversations

```bash
curl -X GET http://localhost:8080/api/conversations \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin_key_789"
```

## Expected Response

Successful message sending returns:
```json
{
  "conversation_id": 1,
  "message_id": null,
  "sent_at": "2025-07-10T04:00:39.835632",
  "status": "sent"
}
```

## Next Steps

- Read the [API Documentation](api/overview.md)
- Learn about [Conversation Management](features/conversations.md)
- Set up [Monitoring](operations/monitoring.md)

## Troubleshooting

### Service won't start
- Check if port 8080 is available: `lsof -i :8080`
- Verify database is running: `make db-up`

### Database connection failed
- Ensure PostgreSQL container is running
- Check connection details in configuration

### API returns 401 Unauthorized
- Include the API key header: `X-API-Key: admin_key_789`

For more help, see the [Troubleshooting Guide](operations/troubleshooting.md).