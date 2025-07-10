# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a **backend interview project scaffold** for Hatch that provides infrastructure for building a unified messaging service. The project is currently in template state - it has complete infrastructure setup and requirements but **no implementation code**.

## Technology Stack
- **Language**: Python 3.11 (compatible with Atheris fuzzing library)
- **Environment Management**: uv (handles both virtual environments and dependencies)
- **Database**: PostgreSQL 15 (Alpine Linux) via Docker Compose
- **Infrastructure**: Docker/Podman for containerization
- **Build System**: Makefile for development tasks
- **Linting**: ruff
- **Testing**: pytest
- **Security Testing**: Atheris coverage-guided fuzzing
- **AI Reasoning**: @sentient-agi-reasoning for deep thinking and analysis

## Common Development Commands

### Python Environment Setup
```bash
uv sync                          # Install dependencies and create virtual environment
uv add <package>                 # Add Python dependencies
uv run <command>                 # Run commands in the uv-managed environment
```

### Development Tools
```bash
uv run ruff check .                     # Run linting
uv run ruff format .                    # Format code
uv run pytest                           # Run unit tests
uv run pytest --cov=. --cov-report=html # Run tests with coverage report
```

### Security Testing
```bash
./bin/validate_security.sh              # Run complete security validation
./bin/run_atheris_fuzz.sh <test_name>   # Run individual Atheris fuzz tests
uv run python tests/security/test_atheris_fuzz.py <test_name> # Direct fuzz test execution
```

### Setup and Database
```bash
make setup          # Initialize project and start database
make db-up          # Start database container
make db-down        # Stop database container
make db-shell       # Connect to database shell
```

### Application Lifecycle
```bash
make run            # Run the application (calls ./bin/start.sh)
make test           # Run API tests (calls ./bin/test.sh)
make clean          # Clean up containers and temporary files
```

### Database Connection
- **Database**: `messaging_service`
- **User**: `messaging_user`
- **Password**: `messaging_password`
- **Port**: `5432`
- **Container**: `messaging-service-db`

## Architecture Overview

### Core Components to Implement
1. **HTTP Server** - Must listen on port 8080
2. **Message Router** - Routes SMS/MMS and email messages
3. **Conversation Manager** - Groups messages by participants
4. **Database Layer** - PostgreSQL with proper relationships and indexing
5. **Provider Integrations** - Mock SMS/MMS and email providers
6. **Webhook Handler** - Processes incoming messages from providers

### Required API Endpoints
- `POST /api/messages/sms` - Send SMS/MMS messages
- `POST /api/messages/email` - Send email messages  
- `POST /api/webhooks/sms` - Receive SMS/MMS webhooks
- `POST /api/webhooks/email` - Receive email webhooks
- `GET /api/conversations` - Get conversations list
- `GET /api/conversations/{id}/messages` - Get messages in conversation

### Key Files
- **`./bin/start.sh`** - Application startup script (must be implemented)
- **`./bin/test.sh`** - Complete API test suite with curl commands
- **`docker-compose.yml`** - Database setup (ready to use)
- **`Makefile`** - Build and development commands

### Data Model Requirements
- **Messages**: Store content, type (SMS/MMS/Email), participants, timestamps
- **Conversations**: Group messages by participants, track metadata
- **Providers**: Mock SMS/MMS and email service integrations
- **Webhooks**: Handle incoming message events

### Development Personas
The project includes detailed persona files in `/personas/` that define roles:
- Developer, System Architect, QA Engineer, Project Manager
- Requirements Analyst, DevOps Engineer, Maintenance Support

## Quality Requirements
- **Test Coverage**: 100% code coverage required
- **Test Results**: 100% tests passing (0 errors, 0 warnings, 0 skipped)
- **Code Quality**: All code must pass ruff linting
- **Personas**: Use `/personas/` files for role-specific tasks
- **No Compromises**: No temporary solutions or simplifications allowed
- **Completion**: All acceptance criteria must be met

## Logging Requirements
- **Persona Thinking**: All persona thinking must be logged to `./logs/<persona>.md`
- **Progress Reports**: Must be written before every context compaction to `./progress/<task>.md`
- **User Prompts**: All user prompts must be logged to `./prompts/user.md`

## Development Workflow
All project tasks must follow a strict 4-phase workflow:

### Phase 1: PLAN (System Architect)
- Use `@sentient-agi-reasoning` for deep analysis
- Create comprehensive technical plans
- Define acceptance criteria
- Authority to reject incomplete requirements

### Phase 2: DO (Developer)
- Implement solutions based on architect's plan
- Follow coding standards and best practices
- Ensure 100% test coverage
- Authority to reject inadequate plans

### Phase 3: CHECK (QA Engineer)
- Validate implementation against acceptance criteria
- Verify test coverage and quality
- Run comprehensive testing
- Authority to reject inadequate implementations

### Phase 4: ACT (Project Manager)
- Coordinate final delivery
- Ensure all requirements met
- Manage stakeholder communication
- Authority to reject incomplete deliverables

**Critical Rules:**
- Each phase has ultimate authority to reject work from previous phase
- No time constraints - work until completion
- Stop and ask user for clarification on complex problems
- No simplifications or temporary solutions allowed

## Implementation Notes
- Application must start via `./bin/start.sh` and listen on port 8080
- Database schema needs to be created from scratch
- All provider integrations should be mocked for this interview project
- Test suite in `./bin/test.sh` provides complete API validation
- Python 3.13.5 with virtualenv, uv, ruff, and pytest stack