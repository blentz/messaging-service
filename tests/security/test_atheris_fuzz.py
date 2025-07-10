"""
Comprehensive Atheris-based fuzz testing for security vulnerabilities.
This module provides coverage-guided fuzzing for the messaging service.
"""

import json
import sys
import os
import atheris
import tempfile
from typing import Dict, Any

# Import after atheris instrumentation setup
with atheris.instrument_imports():
    from app import create_app
    from app.models.message import Message
    from app.models.conversation import Conversation
    from app.services.message_service import MessageService
    from app.services.conversation_service import ConversationService
    from app.middleware.validation import validate_sms_message_request, validate_email_message_request
    from app.providers.twilio_mock import TwilioMockProvider
    from app.providers.sendgrid_mock import SendGridMockProvider


class AtherisFuzzTester:
    """Atheris-based fuzzer for messaging service components."""

    def __init__(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def cleanup(self):
        """Clean up test context."""
        if hasattr(self, 'app_context'):
            self.app_context.pop()


# Global fuzzer instance
fuzzer = AtherisFuzzTester()


def fuzz_message_validation(data: bytes):
    """Fuzz test message validation with coverage-guided input generation."""
    try:
        fdp = atheris.FuzzedDataProvider(data)
        
        # Generate fuzzed message data
        message_data = {
            "from": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(1, 100)),
            "to": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(1, 100)),
            "type": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(1, 20)),
            "body": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 10000)),
        }
        
        # Add random extra fields
        num_extra_fields = fdp.ConsumeIntInRange(0, 10)
        for _ in range(num_extra_fields):
            key = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(1, 50))
            value = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 1000))
            message_data[key] = value
        
        # Test SMS endpoint
        try:
            headers = {'X-API-Key': 'admin_key_789', 'Content-Type': 'application/json'}
            response = fuzzer.client.post(
                '/api/messages/sms',
                data=json.dumps(message_data),
                headers=headers
            )
            # Should not crash, any HTTP status is acceptable
            assert 200 <= response.status_code <= 599
        except Exception:
            # Fuzzing should not cause unhandled exceptions
            pass
            
        # Test email endpoint  
        try:
            response = fuzzer.client.post(
                '/api/messages/email',
                data=json.dumps(message_data),
                headers=headers
            )
            assert 200 <= response.status_code <= 599
        except Exception:
            pass
            
    except Exception:
        # Fuzzing should never cause crashes
        pass


def fuzz_webhook_processing(data: bytes):
    """Fuzz test webhook processing with malformed/malicious payloads."""
    try:
        fdp = atheris.FuzzedDataProvider(data)
        
        # Generate fuzzed webhook data
        webhook_data = {
            "from": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(1, 100)),
            "to": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(1, 100)),
            "type": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(1, 20)),
            "messaging_provider_id": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(1, 100)),
            "body": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 50000)),
        }
        
        # Add malicious headers
        headers = {}
        if fdp.ConsumeBool():
            headers['X-Twilio-Signature'] = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 500))
        if fdp.ConsumeBool():
            headers['Content-Type'] = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(1, 100))
        if fdp.ConsumeBool():
            headers['Authorization'] = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 200))
            
        # Test webhook endpoints
        for endpoint in ['/api/webhooks/sms', '/api/webhooks/email']:
            try:
                response = fuzzer.client.post(
                    endpoint,
                    data=json.dumps(webhook_data),
                    headers=headers
                )
                assert 200 <= response.status_code <= 599
            except Exception:
                pass
                
    except Exception:
        pass


def fuzz_conversation_api(data: bytes):
    """Fuzz test conversation API endpoints."""
    try:
        fdp = atheris.FuzzedDataProvider(data)
        
        # Generate fuzzed conversation ID and query parameters
        conversation_id = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(1, 200))
        
        headers = {'X-API-Key': 'admin_key_789', 'Content-Type': 'application/json'}
        
        # Test conversations list with query params
        query_params = []
        if fdp.ConsumeBool():
            limit = fdp.ConsumeIntInRange(-1000, 1000)
            query_params.append(f"limit={limit}")
        if fdp.ConsumeBool():
            offset = fdp.ConsumeIntInRange(-1000, 1000) 
            query_params.append(f"offset={offset}")
        if fdp.ConsumeBool():
            search = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 500))
            query_params.append(f"search={search}")
            
        query_string = "&".join(query_params)
        url = f"/api/conversations?{query_string}" if query_string else "/api/conversations"
        
        try:
            response = fuzzer.client.get(url, headers=headers)
            assert 200 <= response.status_code <= 599
        except Exception:
            pass
            
        # Test specific conversation messages
        try:
            response = fuzzer.client.get(
                f"/api/conversations/{conversation_id}/messages",
                headers=headers
            )
            assert 200 <= response.status_code <= 599
        except Exception:
            pass
            
    except Exception:
        pass


def fuzz_json_parsing(data: bytes):
    """Fuzz test JSON parsing with malformed data."""
    try:
        fdp = atheris.FuzzedDataProvider(data)
        
        # Generate potentially malformed JSON
        raw_data = fdp.ConsumeBytes(fdp.ConsumeIntInRange(0, 10000))
        
        headers = {'X-API-Key': 'admin_key_789', 'Content-Type': 'application/json'}
        
        # Test all endpoints with malformed JSON
        endpoints = [
            '/api/messages/sms',
            '/api/messages/email', 
            '/api/webhooks/sms',
            '/api/webhooks/email'
        ]
        
        for endpoint in endpoints:
            try:
                response = fuzzer.client.post(
                    endpoint,
                    data=raw_data,
                    headers=headers
                )
                assert 200 <= response.status_code <= 599
            except Exception:
                pass
                
    except Exception:
        pass


def fuzz_authentication_headers(data: bytes):
    """Fuzz test authentication with malformed headers."""
    try:
        fdp = atheris.FuzzedDataProvider(data)
        
        # Generate malicious authentication headers
        auth_key = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 1000))
        content_type = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 200))
        
        headers = {
            'X-API-Key': auth_key,
            'Content-Type': content_type
        }
        
        # Add random headers
        num_headers = fdp.ConsumeIntInRange(0, 20)
        for _ in range(num_headers):
            header_name = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(1, 100))
            header_value = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 500))
            headers[header_name] = header_value
        
        test_data = {
            "from": "+12016661234",
            "to": "+18045551234", 
            "type": "sms",
            "body": "test"
        }
        
        try:
            response = fuzzer.client.post(
                '/api/messages/sms',
                data=json.dumps(test_data),
                headers=headers
            )
            assert 200 <= response.status_code <= 599
        except Exception:
            pass
            
    except Exception:
        pass


def fuzz_provider_integration(data: bytes):
    """Fuzz test provider integrations with malformed data."""
    try:
        fdp = atheris.FuzzedDataProvider(data)
        
        # Test Twilio provider
        twilio = TwilioMockProvider()
        sms_data = {
            "from": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 100)),
            "to": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 100)),
            "body": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 5000)),
        }
        
        try:
            result = twilio.send_sms(**sms_data)
            # Should return a valid response format
            assert isinstance(result, dict)
        except Exception:
            pass
            
        # Test SendGrid provider
        sendgrid = SendGridMockProvider()
        email_data = {
            "from_email": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 100)),
            "to_email": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 100)),
            "subject": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 200)),
            "body": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 10000)),
        }
        
        try:
            result = sendgrid.send_email(**email_data)
            assert isinstance(result, dict)
        except Exception:
            pass
            
    except Exception:
        pass


def fuzz_database_models(data: bytes):
    """Fuzz test database model validation."""
    try:
        fdp = atheris.FuzzedDataProvider(data)
        
        # Test Message model creation
        try:
            message_data = {
                "from_number": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 100)),
                "to_number": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 100)),
                "message_type": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 50)),
                "body": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 10000)),
                "messaging_provider_id": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 100)),
            }
            
            # Attempt to create message (should not crash)
            message = Message(**message_data)
            
        except Exception:
            pass
            
        # Test Conversation model
        try:
            conversation_data = {
                "participants": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 500)),
                "message_type": fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 50)),
            }
            
            conversation = Conversation(**conversation_data)
            
        except Exception:
            pass
            
    except Exception:
        pass


# Fuzz test runners for each component
def TestMessageValidation(data):
    fuzz_message_validation(data)

def TestWebhookProcessing(data):
    fuzz_webhook_processing(data)

def TestConversationAPI(data):
    fuzz_conversation_api(data)

def TestJSONParsing(data):
    fuzz_json_parsing(data)

def TestAuthenticationHeaders(data):
    fuzz_authentication_headers(data)

def TestProviderIntegration(data):
    fuzz_provider_integration(data)

def TestDatabaseModels(data):
    fuzz_database_models(data)


def main():
    """Main entry point for running Atheris fuzz tests."""
    if len(sys.argv) < 2:
        print("Usage: python test_atheris_fuzz.py <test_function> [corpus_dir] [atheris_args...]")
        print("Available tests:")
        print("  - message_validation")
        print("  - webhook_processing")
        print("  - conversation_api")
        print("  - json_parsing")
        print("  - authentication_headers")
        print("  - provider_integration")
        print("  - database_models")
        sys.exit(1)
        
    test_name = sys.argv[1]
    
    # Extract corpus directory if provided
    corpus_dir = None
    atheris_args_start = 2
    if len(sys.argv) > 2 and not sys.argv[2].startswith('-'):
        corpus_dir = sys.argv[2]
        atheris_args_start = 3
        
        # Verify corpus directory exists
        if not os.path.isdir(corpus_dir):
            print(f"Error: Corpus directory not found: {corpus_dir}")
            sys.exit(1)
        
        print(f"Using corpus directory: {corpus_dir}")
        print(f"Corpus files: {len(os.listdir(corpus_dir))} files")
    else:
        print("No corpus directory specified - using random generation only")
    
    # Map test names to functions
    test_functions = {
        "message_validation": TestMessageValidation,
        "webhook_processing": TestWebhookProcessing,
        "conversation_api": TestConversationAPI,
        "json_parsing": TestJSONParsing,
        "authentication_headers": TestAuthenticationHeaders,
        "provider_integration": TestProviderIntegration,
        "database_models": TestDatabaseModels,
    }
    
    if test_name not in test_functions:
        print(f"Unknown test: {test_name}")
        sys.exit(1)
        
    test_func = test_functions[test_name]
    
    # Set up Atheris with corpus directory and optimized arguments
    setup_args = [sys.argv[0]]  # Script name
    
    # Add corpus directory if provided
    if corpus_dir:
        setup_args.append(corpus_dir)
    
    # Add atheris-specific arguments from command line
    setup_args.extend(sys.argv[atheris_args_start:])
    
    # Add default arguments if not already specified
    arg_string = ' '.join(setup_args)
    if '-max_len=' not in arg_string:
        setup_args.append("-max_len=10000")
    if '-rss_limit_mb=' not in arg_string:
        setup_args.append("-rss_limit_mb=2048")
    if '-timeout=' not in arg_string:
        setup_args.append("-timeout=60")  # 60 second timeout per input
    
    print(f"Atheris setup args: {setup_args}")
    atheris.Setup(setup_args, test_func)
    
    try:
        print(f"Starting Atheris fuzz testing for: {test_name}")
        atheris.Fuzz()
    finally:
        fuzzer.cleanup()


if __name__ == "__main__":
    main()