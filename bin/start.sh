#!/bin/bash

# Unified messaging service startup script
# Must listen on port 8080 per requirements
# Uses uv for all dependency and environment management

set -e

echo "Starting unified messaging service..."

# Set environment variables
export FLASK_APP=app
export FLASK_ENV=development
export DATABASE_URL=postgresql://messaging_user:messaging_password@localhost:5432/messaging_service

# Initialize database if needed
echo "Initializing database..."
uv run python -c "
from app import create_app
from app.utils.database import init_db
app = create_app()
init_db(app)
print('Database initialized')
"

echo "Starting Flask application on port 8080..."

# Start the Flask application using uv
uv run flask run --host=0.0.0.0 --port=8080 