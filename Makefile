.PHONY: setup run stop test clean help db-up db-down db-logs db-shell

COMPOSE := "$(which podman-compose || which docker-compose)"

help:
	@echo "Available commands:"
	@echo "  setup    - Set up the project environment and start database"
	@echo "  run      - Run the application"
	@echo "  stop     - Stop the application"
	@echo "  test     - Run tests"
	@echo "  clean    - Clean up temporary files and stop containers"
	@echo "  db-up    - Start the PostgreSQL database"
	@echo "  db-down  - Stop the PostgreSQL database"
	@echo "  db-logs  - Show database logs"
	@echo "  db-shell - Connect to the database shell"
	@echo "  help     - Show this help message"

setup:
	@echo "Setting up the project..."
	@echo "Starting PostgreSQL database..."
	@${COMPOSE} up -d
	@echo "Waiting for database to be ready..."
	@sleep 5
	@echo "Setup complete!"

run:
	@echo "Running the application..."
	@./bin/start.sh

stop:
	@echo "Stopping the application..."
	@./bin/stop.sh

test:
	@echo "Running tests..."
	@echo "Starting test database if not running..."
	@${COMPOSE} up -d
	@echo "Running test script..."
	@./bin/test.sh

clean:
	@echo "Cleaning up..."
	@echo "Stopping and removing containers..."
	@${COMPOSE} down -v
	@echo "Removing any temporary files..."
	@rm -rf *.log *.tmp

db-up:
	@echo "Starting PostgreSQL database..."
	@${COMPOSE} up -d

db-down:
	@echo "Stopping PostgreSQL database..."
	@${COMPOSE} down

db-logs:
	@echo "Showing database logs..."
	@${COMPOSE} logs -f postgres

db-shell:
	@echo "Connecting to database shell..."
	@${COMPOSE} exec postgres psql -U messaging_user -d messaging_service
