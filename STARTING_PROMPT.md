# STARTING_PROMPT.md

## Project Mission
You are tasked with implementing a complete unified messaging service for Hatch's backend interview project. This is a production-quality system that must handle SMS/MMS and Email messaging through a unified API with conversation management and database persistence.

## Project Context
- **Purpose**: Backend interview project scaffold with complete infrastructure
- **Current State**: Template with infrastructure setup but **no implementation code**
- **Technology Stack**: Python 3.13.5, PostgreSQL 15, uv, pytest, ruff
- **Quality Standard**: 100% test coverage, zero compromises, production-ready code

## Core Requirements

### 1. HTTP Service Architecture
- **Port**: Must listen on port 8080
- **Startup**: Must use `./bin/start.sh` script
- **Framework**: Flask web framework (required)
- **ORM**: SQLAlchemy for database operations (required)
- **Authentication**: Flask-Auth for authentication support (minimally functional but secure)
- **Error Handling**: Handle provider errors (500, 429) gracefully
- **Structured Logging**: Implement structured logging for debugging and monitoring (required)
- **Observability**: Expose OpenTelemetry metrics for debugging and monitoring (required)
- **Security**: Critical priority - deep security analysis required at every phase

### 2. Required API Endpoints
All endpoints must be fully functional with proper error handling:

- `POST /api/messages/sms` - Send SMS/MMS messages
- `POST /api/messages/email` - Send email messages  
- `POST /api/webhooks/sms` - Receive SMS/MMS webhooks
- `POST /api/webhooks/email` - Receive email webhooks
- `GET /api/conversations` - Get conversations list
- `GET /api/conversations/{id}/messages` - Get messages in conversation

### 3. Message Formats and Providers

#### SMS/MMS Outbound Format:
```json
{
    "from": "from-phone-number",
    "to": "to-phone-number", 
    "type": "mms" | "sms",
    "body": "text message",
    "attachments": ["attachment-url"] | [] | null,
    "timestamp": "2024-11-01T14:00:00Z"
}
```

#### SMS/MMS Inbound Format (Webhook):
```json
{
    "from": "+18045551234",
    "to": "+12016661234",
    "type": "sms" | "mms",
    "messaging_provider_id": "message-1",
    "body": "text message",
    "attachments": ["attachment-url"] | [] | null,
    "timestamp": "2024-11-01T14:00:00Z"
}
```

#### Email Outbound Format:
```json
{
    "from": "user@usehatchapp.com",
    "to": "contact@gmail.com",
    "body": "text message with or without html",
    "attachments": ["attachment-url"] | [],
    "timestamp": "2024-11-01T14:00:00Z"
}
```

#### Email Inbound Format (Webhook):
```json
{
    "from": "user@usehatchapp.com",
    "to": "contact@gmail.com",
    "xillio_id": "message-2",
    "body": "<html><body>html is <b>allowed</b> here</body></html>",
    "attachments": ["attachment-url"] | [],
    "timestamp": "2024-11-01T14:00:00Z"
}
```

### 4. Database Requirements
- **Database**: PostgreSQL 15 (already configured)
- **Connection**: messaging_service / messaging_user / messaging_password / port 5432
- **Schema**: Must design from scratch with proper relationships and indexing
- **Key Entities**: Messages, Conversations, Providers, Participants
- **Indexing**: Optimize for conversation queries and message retrieval

### 5. Core System Components

#### Message Router
- Route messages to appropriate provider based on type
- Handle message validation and formatting
- Implement retry logic for failed sends

#### Conversation Manager  
- **Default Grouping**: Group messages by individual data points (from/to addresses)
- **Cross-Referenced Filtering**: Provide optional filtering feature for user-requested search across conversation participants
- Support mixed message types (SMS/MMS/Email) in same conversation
- Maintain conversation metadata and timestamps

#### Provider Integrations (Mock)
- **SMS/MMS Provider**: Mock based on Twilio OpenAPI specification (https://www.twilio.com/docs/openapi)
- **Email Provider**: Mock based on SendGrid OpenAPI v3.1 specification (https://github.com/sendgrid/sendgrid-oai)
- **OpenAPI Implementation**: Use OpenAPI parsing library for spec-compliant mocking
- **Error Simulation**: Simulate provider errors (500, 429) for testing
- **Webhook Delivery**: Mock webhook delivery for inbound messages with proper security

#### Webhook Handler
- Process incoming messages from providers
- **Webhook Security**: Implement signature validation and authentication (critical security requirement)
- Handle webhook failures gracefully
- Update conversation state
- **Security Analysis**: Deep security review of all webhook endpoints required

### 6. Data Model Specifications

#### Messages Table
- Content, type (SMS/MMS/Email), participants, timestamps
- Provider-specific IDs (messaging_provider_id, xillio_id)
- Attachment URLs and metadata
- Conversation foreign key relationship

#### Conversations Table
- Participants (normalized from/to addresses)
- Message count and last message timestamp
- Conversation metadata and status

#### Providers Table
- Provider configuration and status
- Mock provider settings
- Error simulation parameters

### 7. Quality Standards (Non-Negotiable)

#### Testing Requirements
- **Coverage**: 100% code coverage required
- **Test Results**: 100% tests passing (0 errors, 0 warnings, 0 skipped)
- **Test Types**: Unit tests, integration tests, API tests
- **Test Data**: Comprehensive edge cases and error scenarios

#### Code Quality
- **Linting**: All code must pass `ruff check .`
- **Formatting**: Code must be formatted with `ruff format .`
- **Standards**: Follow Python best practices and PEP 8
- **Documentation**: Comprehensive docstrings and comments

#### Validation Script
- **Test Suite**: `./bin/test.sh` provides complete API validation
- **Integration**: Must pass all curl-based API tests
- **Performance**: Handle concurrent requests appropriately

## Development Workflow

### Phase 1: PLAN (System Architect)
**Responsibilities:**
- Use `@sentient-agi-reasoning` for deep architectural analysis
- Design comprehensive database schema with relationships
- Define exact API specifications and error handling
- **Security Architecture**: Design secure authentication and webhook validation systems
- **OpenAPI Integration**: Implement provider mocking using openapi-core library
- Create detailed technical architecture document
- Define acceptance criteria for all components
- **Authority**: Reject incomplete requirements

**Deliverables:**
- Complete database schema with DDL
- API specification with request/response formats
- Security architecture design (authentication, webhook validation, input sanitization)
- Observability design (structured logging and OpenTelemetry metrics specification)
- Error handling strategy
- Provider mock implementation plan using openapi-core with Twilio/SendGrid specifications
- Testing strategy and coverage plan
- Fuzz testing strategy specification

### Phase 2: DO (Developer)
**Responsibilities:**
- Implement HTTP server and all API endpoints
- Create database models and migrations
- Implement message routing and conversation management
- Build mock provider integrations using openapi-core
- Develop webhook handling system
- **Implement Observability**: Set up structured logging and OpenTelemetry metrics
- **Security Implementation**: Implement authentication and webhook validation systems
- Ensure 100% test coverage
- **Authority**: Reject inadequate architectural plans

**Deliverables:**
- Complete implementation of all system components
- Structured logging and OpenTelemetry metrics implementation
- Security implementation (authentication, webhook validation)
- Comprehensive test suite with 100% coverage
- Working `./bin/start.sh` script
- Database schema implementation
- Mock provider implementations using openapi-core

### Phase 3: CHECK (QA Engineer)
**Responsibilities:**
- Validate implementation against acceptance criteria
- Verify 100% test coverage and quality
- Run comprehensive testing scenarios
- Validate API functionality with test suite
- Check error handling and edge cases
- **Endpoint Fuzz Testing**: Implement fuzz testing strategy for all API endpoints
- **Security Analysis**: Deep security review of authentication, webhook validation, and all endpoints
- **Authentication Security**: Analyze Flask-Auth implementation for security vulnerabilities
- **Input Validation**: Verify all user inputs are properly sanitized and validated
- **Observability Testing**: Validate structured logging and OpenTelemetry metrics functionality
- **Metrics Validation**: Verify all required metrics are exposed and functioning correctly
- **Authority**: Reject inadequate implementations

**Deliverables:**
- Test execution report with fuzz testing results
- Security analysis report with vulnerability assessment
- Observability validation report (logging and metrics testing)
- Coverage analysis
- Quality assessment
- Bug reports and fixes
- Performance validation
- Authentication security audit

### Phase 4: ACT (Project Manager)
**Responsibilities:**
- Coordinate final delivery
- Ensure all requirements are met
- Validate against original specifications
- Manage quality assurance process
- **Authority**: Reject incomplete deliverables

**Deliverables:**
- Final project delivery
- Quality assurance sign-off
- Documentation review
- Deployment readiness confirmation

## Success Criteria

### Functional Requirements
1. All 6 API endpoints fully operational
2. Message routing working for SMS/MMS and Email
3. Conversation grouping functioning correctly
4. Database persistence with proper relationships
5. Mock providers simulating real-world behavior using OpenAPI specs
6. Webhook processing handling all edge cases
7. Structured logging implemented across all components
8. OpenTelemetry metrics exposed for all specified metrics

### Technical Requirements
1. Application starts via `./bin/start.sh` on port 8080
2. All tests in `./bin/test.sh` pass successfully
3. 100% code coverage achieved
4. All code passes ruff linting
5. Database schema optimized with proper indexes
6. Error handling covers all provider failure scenarios
7. Structured logging functional with JSON formatting
8. OpenTelemetry metrics endpoint accessible and reporting all required metrics

### Quality Requirements
1. Zero compromises or temporary solutions
2. Production-ready code quality
3. Comprehensive documentation
4. Proper error messages and logging
5. Secure webhook handling
6. Scalable architecture design

## Technical Constraints

### Required Technology Stack
- **Language**: Python 3.13.5
- **Web Framework**: Flask (required)
- **ORM**: SQLAlchemy (required)
- **Authentication**: Flask-Auth (required)
- **Structured Logging**: Python logging with JSON formatting (required)
- **Observability**: OpenTelemetry for metrics exposure (required)
- **Environment**: virtualenv with `mkvirtualenv messaging-service`
- **Dependencies**: uv for package management
- **Database**: PostgreSQL 15 (pre-configured)
- **Testing**: pytest with coverage reporting
- **Linting**: ruff for code quality
- **OpenAPI Parsing**: openapi-core (required)

### OpenAPI Parsing Library
**Required Library: openapi-core**
   - Version: 0.19.5 (March 2025)
   - Features: Client/server support for OpenAPI v3.0 and v3.1, validation, unmarshalling
   - Integration: Flask, Django, Werkzeug support
   - Use case: Comprehensive spec compliance and validation
   - Justification: Best integration with Flask and comprehensive validation capabilities

### Observability and Logging Requirements

#### Structured Logging
- **Format**: JSON structured logging for all application logs
- **Fields**: Include timestamp, level, service, endpoint, user_id, conversation_id, message_id
- **Libraries**: Use Python logging with json-logging or structlog
- **Levels**: DEBUG, INFO, WARN, ERROR with appropriate log levels for different scenarios

#### OpenTelemetry Metrics (Demo)
Expose the following common metrics for debugging assistance:

**Message Processing Metrics:**
- `messages_sent_total` (counter) - Total messages sent by type (sms, mms, email)
- `messages_received_total` (counter) - Total messages received by type
- `message_processing_duration_seconds` (histogram) - Time to process messages
- `provider_response_duration_seconds` (histogram) - Provider API response times
- `provider_errors_total` (counter) - Provider errors by type and status code

**API Endpoint Metrics:**
- `http_requests_total` (counter) - HTTP requests by method, endpoint, status
- `http_request_duration_seconds` (histogram) - HTTP request processing time
- `webhook_processing_duration_seconds` (histogram) - Webhook processing time
- `authentication_attempts_total` (counter) - Auth attempts by success/failure

**Database Metrics:**
- `database_queries_total` (counter) - Database queries by operation type
- `database_query_duration_seconds` (histogram) - Database query execution time
- `conversation_creation_total` (counter) - New conversations created
- `active_conversations_gauge` (gauge) - Current active conversations

**System Health Metrics:**
- `application_up` (gauge) - Application health status
- `memory_usage_bytes` (gauge) - Memory usage
- `active_connections_gauge` (gauge) - Active database connections

### Development Commands
```bash
# Environment setup
mkvirtualenv messaging-service
workon messaging-service
uv add flask sqlalchemy flask-auth openapi-core opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-flask structlog
uv sync

# Development workflow
make setup          # Initialize project
make db-up          # Start database
make run            # Start application
make test           # Run tests
ruff check .        # Run linting
ruff format .       # Format code
```

### Infrastructure
- **Database**: messaging_service/messaging_user/messaging_password/5432
- **Container**: messaging-service-db (PostgreSQL 15 Alpine)
- **Startup**: `./bin/start.sh` (must be implemented)
- **Testing**: `./bin/test.sh` (API validation suite)

## Critical Rules

1. **No Compromises**: No temporary solutions or simplifications allowed
2. **Complete Implementation**: All acceptance criteria must be met
3. **Quality First**: 100% test coverage and code quality non-negotiable
4. **Security Priority**: Deep security analysis required at every phase
5. **Phase Authority**: Each phase can reject work from previous phase
6. **Mock Everything**: All external provider integrations must be mocked using OpenAPI specs
7. **Error Handling**: Must handle all provider error scenarios gracefully
8. **Authentication Security**: Minimal but secure authentication implementation required
9. **Webhook Security**: Signature validation and authentication mandatory
10. **Fuzz Testing**: All endpoints must undergo fuzz testing validation
11. **Documentation**: All persona thinking logged to `./logs/<persona>.md`

## Persona Coordination

### Requirements Analyst
- Clarify any ambiguous requirements
- Document detailed specifications
- Validate completeness of requirements

### System Architect  
- Lead Phase 1 (PLAN) with deep technical analysis
- Use `@sentient-agi-reasoning` for architectural decisions
- Create comprehensive technical specifications

### Developer
- Lead Phase 2 (DO) with complete implementation
- Follow architect's specifications exactly
- Ensure 100% test coverage

### QA Engineer
- Lead Phase 3 (CHECK) with thorough validation
- Verify all acceptance criteria met
- Ensure quality standards maintained

### Project Manager
- Lead Phase 4 (ACT) with final coordination
- Ensure all requirements completed
- Coordinate persona interactions

## Next Steps

1. **Requirements Analyst**: Review and clarify any ambiguous requirements
2. **System Architect**: Begin Phase 1 with `@sentient-agi-reasoning` analysis
3. **All Personas**: Log all thinking to respective log files
4. **Project Manager**: Coordinate the 4-phase workflow execution

**Remember**: This is a backend interview project that will be continued during the onsite interview. The implementation must be production-quality, well-understood, and extensible.