# Conversation Management

The Unified Messaging Service automatically groups messages into conversations based on participants, providing a unified view across SMS, MMS, and Email communications.

## How Conversations Work

### Participant-Based Grouping

Messages are grouped into conversations by their participants (from/to addresses):

- **SMS/MMS**: Grouped by phone number pairs
- **Email**: Grouped by email address pairs
- **Cross-Provider**: Same participants across different message types create mixed conversations

### Example Scenarios

#### Single Provider Conversation
```
+12016661234 ↔ +18045551234 (SMS only)
```
Creates an SMS/MMS conversation.

#### Cross-Provider Conversation  
```
user@example.com ↔ contact@gmail.com (Email)
+12016661234 ↔ +18045551234 (SMS)
```
If these represent the same people, they would be separate conversations unless explicitly linked.

#### Mixed Provider Conversation
```
same-user@example.com ↔ same-contact@gmail.com (Email)
same-user-phone ↔ same-contact-phone (SMS)
```
If the system identifies these as the same participants, it creates a mixed conversation.

## Conversation Types

### SMS_MMS
Conversations containing only SMS and/or MMS messages.

```json
{
  "id": 1,
  "conversation_type": "sms_mms",
  "participants": ["+12016661234", "+18045551234"],
  "message_count": 5,
  "last_message_at": "2024-11-01T14:30:00Z"
}
```

### EMAIL
Conversations containing only email messages.

```json
{
  "id": 2, 
  "conversation_type": "email",
  "participants": ["user@example.com", "contact@gmail.com"],
  "message_count": 3,
  "last_message_at": "2024-11-01T14:25:00Z"
}
```

### MIXED
Conversations containing both SMS/MMS and email messages.

```json
{
  "id": 3,
  "conversation_type": "mixed", 
  "participants": ["+12016661234", "user@example.com"],
  "message_count": 8,
  "last_message_at": "2024-11-01T14:35:00Z"
}
```

## Conversation Metadata

### Core Fields

- `id` - Unique conversation identifier
- `conversation_type` - Type: sms_mms, email, or mixed
- `participants` - Array of participant addresses (sorted for consistency)
- `message_count` - Total number of messages in conversation
- `created_at` - When conversation was first created
- `updated_at` - When conversation was last modified
- `last_message_at` - Timestamp of most recent message

### Extended Metadata

- `metadata` - Additional conversation data (custom fields)

```json
{
  "id": 1,
  "conversation_type": "sms_mms",
  "participants": ["+12016661234", "+18045551234"],
  "message_count": 5,
  "created_at": "2024-11-01T14:00:00Z",
  "updated_at": "2024-11-01T14:30:00Z", 
  "last_message_at": "2024-11-01T14:30:00Z",
  "metadata": {
    "tags": ["customer_support"],
    "priority": "high"
  }
}
```

## Automatic Conversation Creation

### When Sending Messages

When you send a message, the system:

1. **Normalizes participants** - Sorts addresses for consistent lookup
2. **Searches for existing conversation** - Looks for conversation with same participants  
3. **Creates new conversation if needed** - If no matching conversation exists
4. **Updates conversation type** - Changes to "mixed" if message type differs
5. **Updates metadata** - Increments message count, updates timestamps

### When Receiving Webhooks

When webhook messages arrive:

1. **Validates webhook signature** - Ensures message is from legitimate provider
2. **Extracts participants** - Gets from/to addresses from webhook payload
3. **Follows same conversation logic** - As sending messages
4. **Stores message** - Adds to appropriate conversation

## Participant Normalization

### Phone Numbers
- Converted to E.164 format (+12016661234)
- Sorted alphabetically for consistency
- Case insensitive comparison

### Email Addresses  
- Converted to lowercase
- Sorted alphabetically for consistency
- Domain validation performed

### Example Normalization
```python
# Input participants (various orders)
["+18045551234", "+12016661234"]
["+12016661234", "+18045551234"] 

# Normalized result (always same order)
["+12016661234", "+18045551234"]
```

## Conversation API Usage

### List All Conversations

```http
GET /api/conversations
X-API-Key: admin_key_789
```

Response:
```json
{
  "conversations": [
    {
      "id": 1,
      "conversation_type": "sms_mms",
      "participants": ["+12016661234", "+18045551234"],
      "message_count": 5,
      "last_message_at": "2024-11-01T14:30:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### Get Conversation Messages

```http
GET /api/conversations/1/messages
X-API-Key: admin_key_789
```

Response:
```json
{
  "conversation_id": 1,
  "messages": [
    {
      "id": 1,
      "message_type": "sms",
      "from": "+12016661234",
      "to": "+18045551234", 
      "body": "Hello!",
      "sent_at": "2024-11-01T14:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

## Advanced Features

### Pagination

All conversation endpoints support pagination:

```http
GET /api/conversations?limit=25&offset=50
GET /api/conversations/1/messages?limit=10&offset=20
```

### Message Filtering

Filter messages by timestamp:

```http
GET /api/conversations/1/messages?since=2024-11-01T14:00:00Z
```

### Search Conversations

Search by participant (future feature):

```http
GET /api/conversations?search=+12016661234
```

## Conversation Lifecycle

### Creation
1. First message between participants creates conversation
2. Conversation type set based on message type
3. Participants normalized and stored

### Updates
1. New messages increment message_count
2. last_message_at updated to newest message timestamp  
3. updated_at reflects last modification
4. Conversation type may change to "mixed"

### Mixed Type Conversion
When a conversation receives a message of different type:
```
SMS conversation + Email message → Mixed conversation
Email conversation + SMS message → Mixed conversation
```

## Performance Considerations

### Indexing
- Conversations indexed by participants for fast lookup
- Messages indexed by conversation_id and timestamp
- Composite indexes for common query patterns

### Caching
- Conversation metadata cached for frequent lookups
- Message counts cached and updated incrementally

### Scalability
- Participant normalization ensures consistent grouping
- Database design optimized for conversation queries
- Pagination prevents large result sets

## Best Practices

### For API Users

1. **Use pagination** for large conversation lists
2. **Filter by timestamp** when syncing messages
3. **Handle mixed conversations** in your UI appropriately
4. **Cache conversation metadata** to reduce API calls

### For Webhook Integration

1. **Validate signatures** on incoming webhooks
2. **Handle duplicate messages** gracefully
3. **Process webhooks asynchronously** for better performance
4. **Monitor webhook failures** and implement retry logic

## Troubleshooting

### Common Issues

**Messages not grouping correctly**
- Check participant normalization
- Verify phone number formats (E.164)
- Ensure email addresses are lowercased

**Conversation type not updating**
- Verify mixed message types are being detected
- Check conversation update logic in logs

**Performance issues**
- Use pagination for large result sets
- Add appropriate database indexes
- Monitor query performance

### Debugging

Enable structured logging to trace conversation operations:
```json
{
  "event": "conversation_created",
  "conversation_id": 1,
  "participants": ["+12016661234", "+18045551234"],
  "message_type": "sms"
}
```

## Next Steps

- [Provider Integration](providers.md) - How messages route to providers
- [Security](security.md) - Authentication and webhook security
- [API Reference](../api/conversations.md) - Complete API documentation