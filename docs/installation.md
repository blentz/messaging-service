# Installation & Setup

Complete installation guide for the Unified Messaging Service.

## System Requirements

### Minimum Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Python**: 3.11 or higher
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Storage**: 1GB free disk space
- **Network**: Internet access for downloading dependencies

### Required Software
- **uv** - Python package manager
- **Docker or Podman** - For PostgreSQL database
- **Git** - For cloning the repository
- **curl** - For testing API endpoints

## Pre-Installation Setup

### 1. Install uv Package Manager

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

**Windows (WSL2):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

**Verify installation:**
```bash
uv --version
```

### 2. Install Docker or Podman

**Docker (recommended):**
- Visit [docker.com](https://docker.com) and install Docker Desktop
- Or on Linux: `sudo apt install docker.io docker-compose`

**Podman (alternative):**
```bash
# Ubuntu/Debian
sudo apt install podman podman-compose

# RHEL/CentOS/Fedora
sudo dnf install podman podman-compose
```

**Verify installation:**
```bash
docker --version
docker-compose --version
```

### 3. Install Git

**Ubuntu/Debian:**
```bash
sudo apt install git
```

**macOS:**
```bash
brew install git
```

**Verify installation:**
```bash
git --version
```

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd messaging-service
```

### 2. Run Setup

```bash
make setup
```

This command:
- Creates Python virtual environment using uv
- Installs all dependencies
- Sets up development environment
- Configures pre-commit hooks

### 3. Start Database

```bash
make db-up
```

This starts a PostgreSQL 15 container with:
- Database: `messaging_service`
- User: `messaging_user`
- Password: `messaging_password` 
- Port: `5432`

**Verify database is running:**
```bash
docker ps | grep postgres
```

### 4. Initialize Database

```bash
make db-init
```

This creates the database schema and tables.

### 5. Start the Service

```bash
make run
```

The service will start on `http://localhost:8080`

### 6. Verify Installation

```bash
make test
```

This runs the complete test suite to verify everything is working.

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://messaging_user:messaging_password@localhost:5432/messaging_service

# Application Configuration  
FLASK_ENV=development
FLASK_DEBUG=true
LOG_LEVEL=INFO

# API Configuration
API_KEY=admin_key_789

# Provider Configuration (for mocking)
TWILIO_ACCOUNT_SID=mock_account_sid
TWILIO_AUTH_TOKEN=mock_auth_token
SENDGRID_API_KEY=mock_sendgrid_key

# Observability
OTEL_METRICS_ENABLED=true
STRUCTURED_LOGGING_ENABLED=true
```

### Application Configuration

Key configuration files:

- `app/config.py` - Main application configuration
- `docker-compose.yml` - Database configuration
- `pyproject.toml` - Python dependencies and tools
- `Makefile` - Development commands

### Database Configuration

Default database settings in `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: messaging_service
      POSTGRES_USER: messaging_user
      POSTGRES_PASSWORD: messaging_password
    ports:
      - "5432:5432"
```

To use a different database:

1. **Update connection string:**
   ```bash
   export DATABASE_URL=postgresql://user:pass@host:port/dbname
   ```

2. **Update docker-compose.yml** with your database settings

## Development Setup

### IDE Configuration

**VS Code:**
1. Install Python extension
2. Select Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Choose the uv virtual environment: `.venv/bin/python`

**PyCharm:**
1. Open project
2. Go to Settings → Project → Python Interpreter
3. Add interpreter from `.venv/bin/python`

### Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

### Testing Setup

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test
uv run pytest tests/integration/test_api_working.py -v
```

### Linting and Formatting

```bash
# Check code style
uv run ruff check .

# Format code
uv run ruff format .

# Type checking
uv run mypy app/
```

## Production Setup

### Docker Deployment

```bash
# Build production image
docker build -t messaging-service .

# Run with production settings
docker run -d \
  --name messaging-service \
  -p 8080:8080 \
  -e DATABASE_URL=postgresql://... \
  -e FLASK_ENV=production \
  messaging-service
```

### Environment Configuration

**Production environment variables:**
```bash
export FLASK_ENV=production
export FLASK_DEBUG=false
export LOG_LEVEL=WARNING
export DATABASE_URL=postgresql://prod_user:prod_pass@prod_host:5432/messaging_service
```

### Security Configuration

**In production:**
1. **Change default API key:**
   ```bash
   export API_KEY=your_secure_api_key_here
   ```

2. **Use secure database credentials:**
   ```bash
   export DATABASE_URL=postgresql://secure_user:secure_password@db_host:5432/messaging_service
   ```

3. **Enable webhook signature validation:**
   ```bash
   export WEBHOOK_SIGNATURE_VALIDATION=true
   ```

### Monitoring Setup

**Metrics collection:**
```bash
export OTEL_METRICS_ENABLED=true
export METRICS_ENDPOINT=http://prometheus:9090
```

**Structured logging:**
```bash
export STRUCTURED_LOGGING_ENABLED=true
export LOG_FORMAT=json
```

## Troubleshooting Installation

### Common Issues

**uv command not found:**
```bash
# Reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

**Docker permission denied:**
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

**Port 8080 already in use:**
```bash
# Find process using port
lsof -i :8080

# Kill process or use different port
export PORT=8081
./bin/start.sh
```

**Database connection failed:**
```bash
# Check if database is running
docker ps | grep postgres

# Restart database
make db-down
make db-up
```

### Verification Steps

**Check all components:**
```bash
# 1. Python environment
uv run python --version

# 2. Dependencies installed
uv run pip list | grep flask

# 3. Database connection
make db-shell -c "SELECT 1;"

# 4. Service health
curl http://localhost:8080/api/conversations -H "X-API-Key: admin_key_789"

# 5. Run tests
make test
```

## Next Steps

After successful installation:

1. **Read the [Quick Start Guide](quickstart.md)** to send your first message
2. **Review [API Documentation](api/overview.md)** to understand the endpoints
3. **Check [Configuration Guide](configuration.md)** for advanced settings
4. **Set up [Monitoring](operations/monitoring.md)** for production use

## Support

For installation issues:
- Check the [Troubleshooting Guide](operations/troubleshooting.md)
- Review system requirements
- Verify all dependencies are installed
- Check log files for error details

**System Information for Support:**
```bash
# Collect system info
uname -a > system_info.txt
python --version >> system_info.txt  
uv --version >> system_info.txt
docker --version >> system_info.txt
```