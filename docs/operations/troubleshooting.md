# Troubleshooting Guide

Common issues and solutions for the Unified Messaging Service.

## Service Won't Start

### Port 8080 Already in Use

**Symptoms:**
```
Address already in use
Port 8080 is in use by another program
```

**Solutions:**
1. **Find the process using port 8080:**
   ```bash
   lsof -i :8080
   netstat -tulpn | grep :8080
   ```

2. **Kill the existing process:**
   ```bash
   kill -9 <PID>
   ```

3. **Or use a different port:**
   ```bash
   export PORT=8081
   ./bin/start.sh
   ```

### Database Connection Failed

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
Connection refused
```

**Solutions:**
1. **Check if database is running:**
   ```bash
   make db-up
   docker ps | grep postgres
   ```

2. **Verify database credentials:**
   ```bash
   echo $DATABASE_URL
   # Should be: postgresql://messaging_user:messaging_password@localhost:5432/messaging_service
   ```

3. **Test database connection:**
   ```bash
   psql postgresql://messaging_user:messaging_password@localhost:5432/messaging_service -c "SELECT 1;"
   ```

### Python Environment Issues

**Symptoms:**
```
ModuleNotFoundError: No module named 'flask'
Command 'uv' not found
```

**Solutions:**
1. **Install uv:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.bashrc
   ```

2. **Sync dependencies:**
   ```bash
   uv sync
   ```

3. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

## API Issues

### 401 Unauthorized

**Symptoms:**
```json
{
  "error": "401 Unauthorized: Missing or invalid API key"
}
```

**Solutions:**
1. **Include API key header:**
   ```bash
   curl -H "X-API-Key: admin_key_789" http://localhost:8080/api/conversations
   ```

2. **Check API key configuration:**
   ```bash
   grep -r "admin_key" app/config.py
   ```

### 422 Validation Error

**Symptoms:**
```json
{
  "error": "Invalid phone number format",
  "code": "VALIDATION_ERROR"
}
```

**Solutions:**
1. **Use E.164 phone number format:**
   ```json
   {
     "from": "+12016661234",  // ✓ Correct
     "to": "18045551234"      // ✗ Missing +
   }
   ```

2. **Validate email addresses:**
   ```json
   {
     "from": "user@example.com",  // ✓ Correct
     "to": "invalid-email"        // ✗ Invalid format
   }
   ```

3. **Check required fields:**
   ```json
   {
     "from": "+12016661234",
     "to": "+18045551234", 
     "type": "sms",           // Required for SMS/MMS
     "body": "Message text",  // Required
     "timestamp": "2024-11-01T14:00:00Z"  // Required
   }
   ```

### 500 Internal Server Error

**Symptoms:**
```json
{
  "error": "Internal server error"
}
```

**Solutions:**
1. **Check application logs:**
   ```bash
   tail -f logs/application.log
   journalctl -u messaging-service -f
   ```

2. **Verify database connectivity:**
   ```bash
   make db-shell
   \dt  # List tables
   ```

3. **Check disk space:**
   ```bash
   df -h
   ```

## Webhook Issues

### Webhook Signature Validation Failed

**Symptoms:**
```json
{
  "error": "401 Unauthorized: Missing X-Twilio-Signature header"
}
```

**Solutions:**
1. **For SMS/MMS webhooks, include Twilio signature:**
   ```bash
   curl -X POST http://localhost:8080/api/webhooks/sms \
     -H "X-Twilio-Signature: valid_signature_here" \
     -H "Content-Type: application/json" \
     -d '{"from": "+18045551234", ...}'
   ```

2. **For Email webhooks, include SendGrid signature:**
   ```bash
   curl -X POST http://localhost:8080/api/webhooks/email \
     -H "X-SendGrid-Signature: valid_signature_here" \
     -H "Content-Type: application/json" \
     -d '{"from": "user@example.com", ...}'
   ```

3. **Check webhook configuration:**
   ```bash
   grep -r "webhook" app/middleware/security.py
   ```

### Webhook Processing Fails

**Symptoms:**
- Webhooks return 200 but messages don't appear in conversations
- Database errors in logs

**Solutions:**
1. **Check webhook payload format:**
   ```json
   // SMS/MMS webhook
   {
     "from": "+18045551234",
     "to": "+12016661234",
     "type": "sms",
     "messaging_provider_id": "message-1",  // Required
     "body": "text message",
     "timestamp": "2024-11-01T14:00:00Z"
   }

   // Email webhook  
   {
     "from": "user@example.com",
     "to": "contact@gmail.com", 
     "xillio_id": "message-2",  // Required
     "body": "email content",
     "timestamp": "2024-11-01T14:00:00Z"
   }
   ```

2. **Verify database transactions:**
   ```bash
   make db-shell
   SELECT COUNT(*) FROM messages;
   SELECT COUNT(*) FROM conversations;
   ```

## Database Issues

### Migration Failures

**Symptoms:**
```
alembic.util.exc.CommandError: Can't locate revision identified by
```

**Solutions:**
1. **Reset database:**
   ```bash
   make db-down
   make db-up
   ```

2. **Initialize database manually:**
   ```bash
   uv run python -c "
   from app import create_app
   from app.utils.database import init_db
   app = create_app()
   init_db(app)
   "
   ```

### Connection Pool Exhausted

**Symptoms:**
```
QueuePool limit of size 5 overflow 10 reached
```

**Solutions:**
1. **Check for connection leaks:**
   ```bash
   grep -r "db.session" app/
   # Ensure all sessions are properly closed
   ```

2. **Increase pool size (temporary fix):**
   ```python
   # In app/config.py
   SQLALCHEMY_ENGINE_OPTIONS = {
       'pool_size': 10,
       'max_overflow': 20
   }
   ```

### Data Corruption

**Symptoms:**
- Inconsistent message counts
- Orphaned messages

**Solutions:**
1. **Check data integrity:**
   ```sql
   -- Connect to database
   SELECT c.id, c.message_count, COUNT(m.id) as actual_count 
   FROM conversations c 
   LEFT JOIN messages m ON c.id = m.conversation_id 
   GROUP BY c.id, c.message_count 
   HAVING c.message_count != COUNT(m.id);
   ```

2. **Fix message counts:**
   ```sql
   UPDATE conversations 
   SET message_count = (
     SELECT COUNT(*) FROM messages 
     WHERE conversation_id = conversations.id
   );
   ```

## Performance Issues

### Slow API Responses

**Symptoms:**
- Response times > 1 second
- Timeout errors

**Diagnostics:**
1. **Check database query performance:**
   ```sql
   EXPLAIN ANALYZE SELECT * FROM conversations ORDER BY last_message_at DESC LIMIT 50;
   ```

2. **Monitor system resources:**
   ```bash
   top
   htop
   iotop
   ```

3. **Check database connections:**
   ```sql
   SELECT * FROM pg_stat_activity WHERE datname = 'messaging_service';
   ```

**Solutions:**
1. **Add missing indexes:**
   ```sql
   CREATE INDEX idx_messages_conversation_timestamp ON messages(conversation_id, sent_at);
   CREATE INDEX idx_conversations_participants ON conversations USING GIN(participants);
   ```

2. **Implement pagination:**
   ```bash
   curl "http://localhost:8080/api/conversations?limit=25&offset=0"
   ```

3. **Add caching (future enhancement):**
   - Redis for conversation metadata
   - Application-level caching for frequent queries

### High Memory Usage

**Symptoms:**
```
MemoryError
Process killed (OOM)
```

**Solutions:**
1. **Monitor memory usage:**
   ```bash
   ps aux | grep python
   free -h
   ```

2. **Reduce batch sizes:**
   ```python
   # In service classes, process in smaller batches
   batch_size = 100  # Instead of loading all at once
   ```

3. **Check for memory leaks:**
   ```bash
   valgrind --tool=memcheck python run.py
   ```

## Security Issues

### Authentication Bypass Attempts

**Symptoms:**
```
401 Unauthorized attempts in logs
Security alerts triggered
```

**Monitoring:**
1. **Check access logs:**
   ```bash
   grep "401" logs/access.log
   grep "Unauthorized" logs/application.log
   ```

2. **Monitor failed authentication:**
   ```bash
   grep "authentication_failed" logs/security.log
   ```

**Mitigation:**
1. **Implement rate limiting:**
   ```python
   # Future enhancement: Add rate limiting middleware
   ```

2. **Monitor suspicious patterns:**
   ```bash
   # Count failed attempts by IP
   grep "401" logs/access.log | awk '{print $1}' | sort | uniq -c | sort -nr
   ```

## Development Issues

### Test Failures

**Symptoms:**
```
FAILED tests/integration/test_api_working.py::test_sms_send
```

**Solutions:**
1. **Run specific test with verbose output:**
   ```bash
   uv run pytest tests/integration/test_api_working.py::test_sms_send -v -s
   ```

2. **Check test database:**
   ```bash
   # Tests use separate test database
   export DATABASE_URL=postgresql://messaging_user:messaging_password@localhost:5432/test_messaging_service
   ```

3. **Reset test environment:**
   ```bash
   make clean
   make setup
   ```

### Coverage Issues

**Symptoms:**
```
Coverage failure: total of 94% is less than fail-under=95%
```

**Solutions:**
1. **Generate coverage report:**
   ```bash
   uv run pytest --cov=. --cov-report=html
   open htmlcov/index.html
   ```

2. **Find uncovered lines:**
   ```bash
   uv run pytest --cov=. --cov-report=term-missing
   ```

## Logging and Monitoring

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
./bin/start.sh
```

### Check Application Logs

```bash
# Structured JSON logs
tail -f logs/application.log | jq

# Error logs
grep ERROR logs/application.log

# Security events
grep security logs/application.log
```

### Monitor Metrics

```bash
# Check if metrics endpoint is available
curl http://localhost:8080/metrics

# Monitor key metrics
curl -s http://localhost:8080/metrics | grep messages_sent_total
```

## Getting Help

### Log Collection

When reporting issues, include:

1. **Application logs:**
   ```bash
   tail -100 logs/application.log > debug_logs.txt
   ```

2. **System information:**
   ```bash
   uname -a > system_info.txt
   python --version >> system_info.txt
   uv --version >> system_info.txt
   ```

3. **Configuration:**
   ```bash
   env | grep -E "(DATABASE|LOG|PORT)" > config.txt
   ```

4. **Database status:**
   ```bash
   docker ps | grep postgres > db_status.txt
   ```

### Useful Commands

```bash
# Health check
curl http://localhost:8080/api/conversations -H "X-API-Key: admin_key_789"

# Database connection test
make db-shell -c "SELECT 1;"

# Full system status
make test

# Clean restart
make clean && make setup && make run
```

For additional support, check the [Operations Guide](deployment.md) and [Development Documentation](../development/architecture.md).