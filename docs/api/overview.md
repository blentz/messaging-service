# API Overview

The Unified Messaging Service provides a REST API for sending and receiving messages across multiple providers (SMS/MMS and Email) with automatic conversation management.

## Base URL

```
http://localhost:8080
```

## Authentication

All API requests require an API key in the header:

```http
X-API-Key: admin_key_789
```

## API Endpoints

### Message Endpoints
- `POST /api/messages/sms` - Send SMS/MMS messages
- `POST /api/messages/email` - Send email messages

### Webhook Endpoints  
- `POST /api/webhooks/sms` - Receive SMS/MMS webhooks from providers
- `POST /api/webhooks/email` - Receive email webhooks from providers

### Conversation Endpoints
- `GET /api/conversations` - List conversations
- `GET /api/conversations/{id}/messages` - Get messages in a conversation

## Content Type

All endpoints expect and return JSON:

```http
Content-Type: application/json
```

## Message Types

The service supports three message types:
- **SMS**: Text messages via SMS provider
- **MMS**: Multimedia messages via SMS provider  
- **Email**: Email messages via email provider

## Response Format

### Success Response
```json
{
  "conversation_id": 1,
  "message_id": null,
  "sent_at": "2025-07-10T04:00:39.835632", 
  "status": "sent"
}
```

### Error Response
```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": {}
}
```

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid API key
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Rate Limiting

Currently no rate limiting is implemented. In production, consider implementing rate limiting based on API key.

## Webhooks Security

Webhook endpoints require provider-specific signature validation:
- SMS/MMS webhooks require `X-Twilio-Signature` header
- Email webhooks require `X-SendGrid-Signature` header

## Pagination

List endpoints support pagination:
- `limit` - Number of items per page (default: 50, max: 100)
- `offset` - Number of items to skip (default: 0)

Example:
```
GET /api/conversations?limit=25&offset=50
```

## Filtering

Conversation messages support filtering:
- `since` - ISO 8601 timestamp to filter messages after

Example:
```
GET /api/conversations/1/messages?since=2024-11-01T14:00:00Z
```

## Next Steps

- [Message Endpoints](messages.md) - Detailed message API documentation
- [Webhook Endpoints](webhooks.md) - Webhook API documentation  
- [Conversation Endpoints](conversations.md) - Conversation API documentation
- [Authentication](authentication.md) - Authentication details
- [Error Handling](errors.md) - Error codes and troubleshooting