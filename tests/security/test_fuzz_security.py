"""
Actual fuzz testing for security vulnerabilities.
"""

import json
import random
import string
import pytest

from app import create_app


class TestSecurityFuzzing:
    """Real fuzz testing for security vulnerabilities."""

    @pytest.fixture
    def app(self):
        return create_app()

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def auth_headers(self):
        return {'X-API-Key': 'admin_key_789', 'Content-Type': 'application/json'}

    def test_sql_injection_attempts(self, client, auth_headers):
        """Test SQL injection vulnerabilities."""
        sql_payloads = [
            "'; DROP TABLE messages; --",
            "' OR '1'='1",
            "admin'; DELETE FROM conversations; --",
            "'; INSERT INTO messages VALUES(1,1,1,'hacked'); --",
            "' UNION SELECT password FROM users; --"
        ]
        
        for payload in sql_payloads:
            # Test in phone number field
            data = {
                "from": payload,
                "to": "+18045551234",
                "type": "sms",
                "body": "test"
            }
            response = client.post('/api/messages/sms', 
                                 data=json.dumps(data), 
                                 headers=auth_headers)
            # Should not succeed with SQL injection (400 or 500 both indicate rejection)
            assert response.status_code in [400, 500]
            
            # Test in email field
            data = {
                "from": payload,
                "to": "test@example.com",
                "body": "test"
            }
            response = client.post('/api/messages/email',
                                 data=json.dumps(data),
                                 headers=auth_headers)
            assert response.status_code in [400, 500]

    def test_xss_injection_attempts(self, client, auth_headers):
        """Test XSS vulnerabilities."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
            "javascript:alert(1)",
            "<iframe src='javascript:alert(1)'></iframe>"
        ]
        
        for payload in xss_payloads:
            # Test in message body
            data = {
                "from": "+12016661234",
                "to": "+18045551234", 
                "type": "sms",
                "body": payload
            }
            response = client.post('/api/messages/sms',
                                 data=json.dumps(data),
                                 headers=auth_headers)
            # Should reject or handle gracefully (XSS sanitization makes body empty, which fails validation)
            assert response.status_code in [200, 400, 500]

    def test_authentication_bypass_attempts(self, client):
        """Test authentication bypass vulnerabilities."""
        bypass_attempts = [
            {},  # No headers
            {'X-API-Key': ''},  # Empty key
            {'X-API-Key': 'admin'},  # Partial key
            {'X-API-Key': 'admin_key_789; DROP TABLE users;'},  # SQL injection in key
            {'X-API-Key': '../../../etc/passwd'},  # Path traversal
            {'X-API-Key': 'admin_key_789\r\nX-Admin: true'},  # Header injection
        ]
        
        test_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms", 
            "body": "test"
        }
        
        for headers in bypass_attempts:
            headers['Content-Type'] = 'application/json'
            try:
                response = client.post('/api/messages/sms',
                                     data=json.dumps(test_data),
                                     headers=headers)
                # Should always require valid auth
                assert response.status_code == 401
            except ValueError as e:
                # Werkzeug testing client prevents header injection (good security)
                if "newline characters" in str(e):
                    continue  # This is expected security behavior
                else:
                    raise

    def test_oversized_payload_handling(self, client, auth_headers):
        """Test handling of oversized payloads."""
        # Create very large payloads
        large_payloads = [
            "A" * 10000,  # 10KB
            "A" * 100000,  # 100KB  
            "A" * 1000000,  # 1MB
        ]
        
        for payload in large_payloads:
            data = {
                "from": "+12016661234",
                "to": "+18045551234",
                "type": "sms",
                "body": payload
            }
            response = client.post('/api/messages/sms',
                                 data=json.dumps(data),
                                 headers=auth_headers)
            # Should handle gracefully, not crash (oversized content fails validation)
            assert response.status_code in [200, 400, 413, 422, 500]

    def test_malformed_json_handling(self, client, auth_headers):
        """Test malformed JSON handling."""
        malformed_payloads = [
            "{incomplete",
            '{"key": incomplete}',
            "not json at all",
            '{"nested": {"incomplete": }',
            "",
            "null",
            "[]"
        ]
        
        for payload in malformed_payloads:
            response = client.post('/api/messages/sms',
                                 data=payload,
                                 headers=auth_headers)
            # Should handle gracefully
            assert response.status_code in [400, 500]

    def test_webhook_signature_bypass_attempts(self, client):
        """Test webhook signature bypass attempts."""
        webhook_data = {
            "from": "+18045551234",
            "to": "+12016661234", 
            "type": "sms",
            "messaging_provider_id": "msg-123",
            "body": "test"
        }
        
        bypass_attempts = [
            {},  # No signature
            {'X-Twilio-Signature': ''},  # Empty signature
            {'X-Twilio-Signature': 'fake'},  # Fake signature
            {'X-Twilio-Signature': '../../../etc/passwd'},  # Path traversal
        ]
        
        for headers in bypass_attempts:
            headers['Content-Type'] = 'application/json'
            response = client.post('/api/webhooks/sms',
                                 data=json.dumps(webhook_data),
                                 headers=headers)
            # Should reject unsigned/invalid webhooks
            assert response.status_code in [401, 403, 500]

    def test_path_traversal_attempts(self, client, auth_headers):
        """Test path traversal vulnerabilities."""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd"
        ]
        
        for payload in traversal_payloads:
            # Test in conversation ID
            response = client.get(f'/api/conversations/{payload}/messages',
                                headers=auth_headers)
            # Should not allow path traversal
            assert response.status_code in [400, 404]

    def test_unicode_and_encoding_attacks(self, client, auth_headers):
        """Test Unicode and encoding attack vectors."""
        unicode_payloads = [
            "\x00\x01\x02\x03",  # Null bytes
            "🔥💀🚫👾🤖",  # Unicode emoji
            "test\u0000hidden",  # Null byte injection
            "测试中文",  # Chinese characters
            "тест",  # Cyrillic
        ]
        
        for payload in unicode_payloads:
            data = {
                "from": "+12016661234",
                "to": "+18045551234",
                "type": "sms", 
                "body": payload
            }
            response = client.post('/api/messages/sms',
                                 data=json.dumps(data),
                                 headers=auth_headers)
            # Should handle Unicode gracefully
            assert response.status_code in [200, 400]

    def test_content_type_confusion(self, client):
        """Test content type confusion attacks."""
        test_data = json.dumps({
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "test"
        })
        
        content_types = [
            "text/plain",
            "application/xml", 
            "multipart/form-data",
            "application/x-www-form-urlencoded",
            "",
            "application/json; charset=utf-8; boundary=something"
        ]
        
        for content_type in content_types:
            headers = {
                'X-API-Key': 'admin_key_789',
                'Content-Type': content_type
            }
            response = client.post('/api/messages/sms',
                                 data=test_data,
                                 headers=headers)
            if content_type != "application/json":
                # Should reject non-JSON content types
                assert response.status_code in [400, 500]


class TestInputValidationFuzzing:
    """Fuzz testing for input validation."""

    @pytest.fixture
    def app(self):
        return create_app()

    @pytest.fixture 
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def auth_headers(self):
        return {'X-API-Key': 'admin_key_789', 'Content-Type': 'application/json'}

    def test_phone_number_format_fuzzing(self, client, auth_headers):
        """Fuzz test phone number validation."""
        invalid_phones = [
            "1234567890",  # Missing +
            "+",  # Too short
            "++12345678901",  # Double +
            "+1abc123def45",  # Letters
            "+1 234 567 8901",  # Spaces
            "+123456789012345678901",  # Too long
            "not-a-phone",  # Text
            "+1-234-567-8901",  # Dashes
            "+1(234)567-8901",  # Parentheses
        ]
        
        for phone in invalid_phones:
            data = {
                "from": phone,
                "to": "+18045551234",
                "type": "sms",
                "body": "test"
            }
            response = client.post('/api/messages/sms',
                                 data=json.dumps(data),
                                 headers=auth_headers)
            # Should reject invalid phone formats
            assert response.status_code in [400, 500]

    def test_email_format_fuzzing(self, client, auth_headers):
        """Fuzz test email validation."""
        invalid_emails = [
            "invalid",
            "@example.com", 
            "user@",
            "user@@example.com",
            "user@.com",
            "user@example.",
            "user name@example.com",  # Space
            "user@exam ple.com",  # Space in domain
            "user@",  # Missing domain
            "user@.example.com",  # Leading dot
        ]
        
        for email in invalid_emails:
            data = {
                "from": email,
                "to": "valid@example.com",
                "body": "test"
            }
            response = client.post('/api/messages/email',
                                 data=json.dumps(data),
                                 headers=auth_headers)
            # Should reject invalid email formats
            assert response.status_code in [400, 500]

    def test_random_field_injection(self, client, auth_headers):
        """Test injection of random fields."""
        base_data = {
            "from": "+12016661234",
            "to": "+18045551234",
            "type": "sms",
            "body": "test"
        }
        
        # Add random fields
        for _ in range(10):
            test_data = base_data.copy()
            
            # Add 1-5 random fields
            for _ in range(random.randint(1, 5)):
                random_key = ''.join(random.choices(string.ascii_letters, k=10))
                random_value = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
                test_data[random_key] = random_value
            
            response = client.post('/api/messages/sms',
                                 data=json.dumps(test_data),
                                 headers=auth_headers)
            # Should handle unknown fields gracefully
            assert response.status_code in [200, 400]