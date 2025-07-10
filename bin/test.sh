#!/bin/bash

# Test script for messaging service endpoints
# This script tests the local messaging service using the JSON examples from README.md

BASE_URL="http://localhost:8080"
CONTENT_TYPE="Content-Type: application/json"
API_KEY="X-API-Key: admin_key_789"
TIMESTAMP=$(date --iso-8601='sec' -u | sed 's/+00:00/Z/')

# Function to generate HMAC-SHA1 signature for Twilio
generate_twilio_signature() {
    local url="$1"
    local data="$2"
    local secret="twilio-webhook-secret"
    echo -n "${url}${data}" | openssl dgst -sha1 -hmac "$secret" -binary | base64
}

# Function to generate HMAC-SHA256 signature for SendGrid
generate_sendgrid_signature() {
    local data="$1"
    local secret="sendgrid-webhook-secret"
    echo -n "$data" | openssl dgst -sha256 -hmac "$secret" | cut -d' ' -f2
}

# "timestamp": "2024-11-01T14:00:00Z"
echo "=== Testing Messaging Service Endpoints ==="
echo "Base URL: $BASE_URL"
echo "TIMESTAMP: $TIMESTAMP"
echo

# Test 1: Send SMS
echo "1. Testing SMS send..."
curl -X POST "$BASE_URL/api/messages/sms" \
  -H "$CONTENT_TYPE" \
  -H "$API_KEY" \
  -d "{
    \"from\": \"+12016661234\",
    \"to\": \"+18045551234\",
    \"type\": \"sms\",
    \"body\": \"Hello! This is a test SMS message.\",
    \"attachments\": null,
    \"timestamp\": \"${TIMESTAMP}\"
  }" \
  -w "\nStatus: %{http_code}\n\n"

# Test 2: Send MMS
echo "2. Testing MMS send..."
curl -X POST "$BASE_URL/api/messages/sms" \
  -H "$CONTENT_TYPE" \
  -H "$API_KEY" \
  -d "{
    \"from\": \"+12016661234\",
    \"to\": \"+18045551234\",
    \"type\": \"mms\",
    \"body\": \"Hello! This is a test MMS message with attachment.\",
    \"attachments\": [\"https://example.com/image.jpg\"],
    \"timestamp\": \"${TIMESTAMP}\"
  }" \
  -w "\nStatus: %{http_code}\n\n"

# Test 3: Send Email
echo "3. Testing Email send..."
curl -X POST "$BASE_URL/api/messages/email" \
  -H "$CONTENT_TYPE" \
  -H "$API_KEY" \
  -d "{
    \"from\": \"user@usehatchapp.com\",
    \"to\": \"contact@gmail.com\",
    \"body\": \"Hello! This is a test email message with <b>HTML</b> formatting.\",
    \"attachments\": [\"https://example.com/document.pdf\"],
    \"timestamp\": \"${TIMESTAMP}\"
  }" \
  -w "\nStatus: %{http_code}\n\n"

# Test 4: Simulate incoming SMS webhook
echo "4. Testing incoming SMS webhook..."
SMS_WEBHOOK_DATA="{
    \"from\": \"+18045551234\",
    \"to\": \"+12016661234\",
    \"type\": \"sms\",
    \"messaging_provider_id\": \"message-1\",
    \"body\": \"This is an incoming SMS message\",
    \"attachments\": null,
    \"timestamp\": \"${TIMESTAMP}\"
  }"
TWILIO_SIGNATURE=$(generate_twilio_signature "$BASE_URL/api/webhooks/sms" "$SMS_WEBHOOK_DATA")
curl -X POST "$BASE_URL/api/webhooks/sms" \
  -H "$CONTENT_TYPE" \
  -H "X-Twilio-Signature: $TWILIO_SIGNATURE" \
  -d "$SMS_WEBHOOK_DATA" \
  -w "\nStatus: %{http_code}\n\n"

# Test 5: Simulate incoming MMS webhook
echo "5. Testing incoming MMS webhook..."
MMS_WEBHOOK_DATA="{
    \"from\": \"+18045551234\",
    \"to\": \"+12016661234\",
    \"type\": \"mms\",
    \"messaging_provider_id\": \"message-2\",
    \"body\": \"This is an incoming MMS message\",
    \"attachments\": [\"https://example.com/received-image.jpg\"],
    \"timestamp\": \"${TIMESTAMP}\"
  }"
TWILIO_SIGNATURE_MMS=$(generate_twilio_signature "$BASE_URL/api/webhooks/sms" "$MMS_WEBHOOK_DATA")
curl -X POST "$BASE_URL/api/webhooks/sms" \
  -H "$CONTENT_TYPE" \
  -H "X-Twilio-Signature: $TWILIO_SIGNATURE_MMS" \
  -d "$MMS_WEBHOOK_DATA" \
  -w "\nStatus: %{http_code}\n\n"

# Test 6: Simulate incoming Email webhook
echo "6. Testing incoming Email webhook..."
EMAIL_WEBHOOK_DATA="{
    \"from\": \"contact@gmail.com\",
    \"to\": \"user@usehatchapp.com\",
    \"xillio_id\": \"message-3\",
    \"body\": \"<html><body>This is an incoming email with <b>HTML</b> content</body></html>\",
    \"attachments\": [\"https://example.com/received-document.pdf\"],
    \"timestamp\": \"${TIMESTAMP}\"
  }"
SENDGRID_SIGNATURE=$(generate_sendgrid_signature "$EMAIL_WEBHOOK_DATA")
curl -X POST "$BASE_URL/api/webhooks/email" \
  -H "$CONTENT_TYPE" \
  -H "X-SendGrid-Signature: $SENDGRID_SIGNATURE" \
  -d "$EMAIL_WEBHOOK_DATA" \
  -w "\nStatus: %{http_code}\n\n"

# Test 7: Get conversations
echo "7. Testing get conversations..."
curl -X GET "$BASE_URL/api/conversations" \
  -H "$CONTENT_TYPE" \
  -H "$API_KEY" \
  -w "\nStatus: %{http_code}\n\n"

# Test 8: Get messages for a conversation (example conversation ID)
echo "8. Testing get messages for conversation..."
curl -X GET "$BASE_URL/api/conversations/1/messages" \
  -H "$CONTENT_TYPE" \
  -H "$API_KEY" \
  -w "\nStatus: %{http_code}\n\n"

echo "=== Test script completed ===" 
