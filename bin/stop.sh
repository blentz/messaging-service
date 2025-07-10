#!/bin/bash

# Unified messaging service shutdown script
# Stops the Flask application and optionally the database

set -e

echo "Stopping unified messaging service..."

# Find and kill Flask processes running on port 8080
echo "Stopping Flask application..."
FLASK_PID=$(lsof -t -i:8080 2>/dev/null || true)
if [ -n "$FLASK_PID" ]; then
    echo "Found Flask process(es) with PID: $FLASK_PID"
    kill -TERM $FLASK_PID
    sleep 2
    # Check if process is still running and force kill if needed
    if kill -0 $FLASK_PID 2>/dev/null; then
        echo "Process still running, force killing..."
        kill -KILL $FLASK_PID
    fi
    echo "Flask application stopped"
else
    echo "No Flask application found running on port 8080"
fi

# Stop database if --db flag is provided
if [ "$1" = "--db" ]; then
    echo "Stopping PostgreSQL database..."
    podman-compose down
    echo "Database stopped"
fi

echo "Shutdown complete!"