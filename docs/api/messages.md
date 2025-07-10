# Message Endpoints

Send SMS, MMS, and Email messages through the unified messaging API.

## Send SMS Message

Send an SMS message to a phone number.

**Endpoint:** `POST /api/messages/sms`

### Request

```http
POST /api/messages/sms
Content-Type: application/json
X-API-Key: admin_key_789

{
  "from": "+12016661234",
  "to": "+18045551234", 
  "type": "sms",
  "body": "Hello! This is a test SMS message.",
  "attachments": null,
  "timestamp": "2024-11-01T14:00:00Z"
}
```

### Required Fields

- `from` (string) - Sender phone number in E.164 format
- `to` (string) - Recipient phone number in E.164 format  
- `type` (string) - Message type: "sms" or "mms"
- `body` (string) - Message text content
- `timestamp` (string) - ISO 8601 UTC timestamp

### Optional Fields

- `attachments` (array|null) - Array of attachment URLs (required for MMS, null for SMS)

### Response

```json
{
  "conversation_id": 1,
  "message_id": null,
  "sent_at": "2025-07-10T04:00:39.835632",
  "status": "sent"
}
```

## Send MMS Message

Send an MMS message with attachments.

**Endpoint:** `POST /api/messages/sms`

### Request

```http
POST /api/messages/sms
Content-Type: application/json
X-API-Key: admin_key_789

{
  "from": "+12016661234",
  "to": "+18045551234",
  "type": "mms", 
  "body": "Check out this image!",
  "attachments": ["https://example.com/image.jpg"],
  "timestamp": "2024-11-01T14:00:00Z"
}
```

### MMS Requirements

- `type` must be "mms"
- `attachments` must be an array with at least one URL
- Attachment URLs must be valid HTTP/HTTPS URLs

## Send Email Message

Send an email message.

**Endpoint:** `POST /api/messages/email`

### Request

```http
POST /api/messages/email
Content-Type: application/json
X-API-Key: admin_key_789

{
  "from": "user@usehatchapp.com",
  "to": "contact@gmail.com",
  "body": "Hello! This is a test email with <b>HTML</b> formatting.",
  "attachments": ["https://example.com/document.pdf"],
  "timestamp": "2024-11-01T14:00:00Z"
}
```

### Required Fields

- `from` (string) - Sender email address
- `to` (string) - Recipient email address
- `body` (string) - Email content (HTML or plain text)
- `timestamp` (string) - ISO 8601 UTC timestamp

### Optional Fields

- `attachments` (array) - Array of attachment URLs (can be empty array)

### Email Features

- HTML content is supported in the body
- Multiple attachments are supported
- Email addresses are validated for proper format

## Validation Rules

### Phone Numbers
- Must be in E.164 format (e.g., +12016661234)
- Must start with + and country code
- Length: 10-15 digits after country code

### Email Addresses
- Must be valid email format
- Domain validation is performed
- Case insensitive

### Attachments
- URLs must be valid HTTP/HTTPS format
- Maximum 10 attachments per message
- Each URL must be accessible

### Message Body
- Maximum length: 1600 characters for SMS
- No length limit for email
- Special characters are supported

### Timestamps
- Must be valid ISO 8601 format
- Must include timezone (Z for UTC recommended)
- Future timestamps are allowed

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid phone number format",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "from",
    "value": "invalid-phone"
  }
}
```

### 422 Unprocessable Entity
```json
{
  "error": "SMS messages cannot have attachments",
  "code": "VALIDATION_ERROR", 
  "details": {
    "field": "attachments",
    "message_type": "sms"
  }
}
```

## Provider Integration

Messages are routed to appropriate providers:
- **SMS/MMS**: Routed to Twilio mock provider
- **Email**: Routed to SendGrid mock provider

Provider errors are handled gracefully:
- 500 errors: Message marked as failed, retry logic applied
- 429 errors: Rate limiting, automatic retry with backoff

## Conversation Management

Messages automatically create or join conversations based on participants:
- SMS/MMS: Grouped by phone number pairs
- Email: Grouped by email address pairs  
- Cross-provider: Same participants across different message types create mixed conversations

## Examples

### Simple SMS
```bash
curl -X POST http://localhost:8080/api/messages/sms \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin_key_789" \
  -d '{
    "from": "+12016661234",
    "to": "+18045551234",
    "type": "sms", 
    "body": "Hello!",
    "attachments": null,
    "timestamp": "2024-11-01T14:00:00Z"
  }'
```

### MMS with Image
```bash
curl -X POST http://localhost:8080/api/messages/sms \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin_key_789" \
  -d '{
    "from": "+12016661234",
    "to": "+18045551234", 
    "type": "mms",
    "body": "Check this out!",
    "attachments": ["https://example.com/photo.jpg"],
    "timestamp": "2024-11-01T14:00:00Z"
  }'
```

### HTML Email
```bash
curl -X POST http://localhost:8080/api/messages/email \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin_key_789" \
  -d '{
    "from": "sender@example.com",
    "to": "recipient@example.com",
    "body": "<h1>Hello!</h1><p>This is an <b>HTML</b> email.</p>",
    "attachments": [],
    "timestamp": "2024-11-01T14:00:00Z"
  }'
```

## Next Steps

- [Webhook Endpoints](webhooks.md) - Receiving inbound messages
- [Conversation Endpoints](conversations.md) - Managing conversations
- [Error Handling](errors.md) - Complete error reference