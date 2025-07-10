#!/bin/bash

# Individual Atheris Fuzz Test Runner
# Uses uv for all dependency and environment management
# Usage: ./bin/run_atheris_fuzz.sh <test_name> [duration_seconds]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <test_name> [duration_seconds]"
    echo
    echo "Available test names:"
    echo "  - message_validation"
    echo "  - webhook_processing"
    echo "  - conversation_api"
    echo "  - json_parsing"
    echo "  - authentication_headers"
    echo "  - provider_integration"
    echo "  - database_models"
    echo
    echo "Examples:"
    echo "  $0 message_validation 90        # Run for 90 seconds (minimum recommended)"
    echo "  $0 json_parsing 120             # Run for 2 minutes"
    echo "  $0 webhook_processing 0         # Run until manually stopped"
    exit 1
fi

TEST_NAME="$1"
DURATION="${2:-90}"  # Default to 90 seconds minimum

# Validate test name
VALID_TESTS=("message_validation" "webhook_processing" "conversation_api" "json_parsing" "authentication_headers" "provider_integration" "database_models")

if [[ ! " ${VALID_TESTS[@]} " =~ " ${TEST_NAME} " ]]; then
    print_error "Invalid test name: $TEST_NAME"
    print_error "Valid tests: ${VALID_TESTS[*]}"
    exit 1
fi

print_status "=========================================="
print_status "Atheris Fuzz Test Runner"
print_status "=========================================="
print_status "Test: $TEST_NAME"
if [ "$DURATION" -eq 0 ]; then
    print_status "Duration: Unlimited (Ctrl+C to stop)"
else
    print_status "Duration: $DURATION seconds (minimum 90s recommended)"
fi
print_status "=========================================="

# Check if database is running
print_status "Checking database connectivity..."
if ! podman ps | grep -q "messaging-service-db"; then
    print_status "Starting database..."
    podman run -d --name messaging-service-db -p 5432:5432 -e POSTGRES_DB=messaging_service -e POSTGRES_USER=messaging_user -e POSTGRES_PASSWORD=messaging_password postgres:15-alpine
    sleep 10
fi

# Check if app is running
print_status "Checking if application is running..."
if ! curl -s http://localhost:8080/health >/dev/null 2>&1; then
    print_status "Starting application..."
    ./bin/start.sh &
    APP_PID=$!
    sleep 10
    
    # Wait for app to be ready
    for i in {1..30}; do
        if curl -s http://localhost:8080/health >/dev/null 2>&1; then
            print_success "Application is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Application failed to start"
            exit 1
        fi
        sleep 2
    done
else
    print_success "Application is already running"
fi

# Ensure atheris is available
print_status "Ensuring Atheris is available..."
export LIBFUZZER_LIB=/usr/lib/clang/20/lib/x86_64-redhat-linux-gnu/libclang_rt.fuzzer.a
uv add atheris >/dev/null 2>&1 || true

# Create results directory
RESULTS_DIR="atheris_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

print_status "Results will be saved to: $RESULTS_DIR/"

# Run the fuzz test
print_status "Starting Atheris fuzz test: $TEST_NAME"
echo

# Prepare command with corpus directory
CORPUS_DIR="tests/security/corpus/$TEST_NAME"
if [ ! -d "$CORPUS_DIR" ]; then
    print_error "Corpus directory not found: $CORPUS_DIR"
    print_status "Available corpus directories:"
    ls -la tests/security/corpus/ 2>/dev/null || echo "  No corpus directories found"
    exit 1
fi

print_status "Using corpus directory: $CORPUS_DIR"

# Build atheris command with corpus directory and optimized parameters
FUZZ_CMD="uv run python tests/security/test_atheris_fuzz.py $TEST_NAME $CORPUS_DIR -max_len=10000 -rss_limit_mb=2048"

if [ "$DURATION" -gt 0 ]; then
    # Warn if duration is less than 90 seconds
    if [ "$DURATION" -lt 90 ]; then
        print_warning "Duration is less than 90 seconds - may not provide adequate coverage"
        print_warning "Recommended minimum: 90 seconds for effective fuzzing"
    fi
    timeout_cmd="timeout ${DURATION}s"
    FUZZ_CMD="$timeout_cmd $FUZZ_CMD"
fi

# Create a comprehensive log
{
    echo "================================================="
    echo "ATHERIS FUZZ TEST EXECUTION LOG"
    echo "================================================="
    echo "Test Name: $TEST_NAME"
    echo "Start Time: $(date)"
    echo "Duration: ${DURATION}s (0 = unlimited)"
    echo "Command: $FUZZ_CMD"
    echo "Working Directory: $(pwd)"
    echo "Environment Manager: uv"
    echo "Python Version: $(uv run python --version 2>&1)"
    echo "Atheris Version: $(uv run python -c 'import atheris; print(\"Available\")' 2>/dev/null || echo 'Unknown')"
    echo "================================================="
    echo
    
    # Set environment variables for reproducible fuzzing
    export ATHERIS_RUNS=1000000  # High number of runs
    export ATHERIS_MAX_LEN=10000  # Maximum input length
    
    # Run the actual fuzz test
    eval "$FUZZ_CMD" 2>&1 || {
        exit_code=$?
        echo
        echo "================================================="
        echo "FUZZ TEST COMPLETED"
        echo "================================================="
        echo "End Time: $(date)"
        if [ $exit_code -eq 124 ]; then
            echo "Status: COMPLETED (timeout reached)"
            print_success "Fuzz test completed successfully (timeout reached)"
        elif [ $exit_code -eq 130 ]; then
            echo "Status: INTERRUPTED (Ctrl+C)"
            print_status "Fuzz test interrupted by user"
        else
            echo "Status: EXITED (code: $exit_code)"
            if [ $exit_code -eq 0 ]; then
                print_success "Fuzz test completed successfully"
            else
                print_error "Fuzz test exited with error code: $exit_code"
            fi
        fi
        exit $exit_code
    }
    
} 2>&1 | tee "$RESULTS_DIR/atheris_${TEST_NAME}_$(date +%H%M%S).log"

# Save additional information
{
    echo "SYSTEM INFORMATION"
    echo "=================="
    echo "Date: $(date)"
    echo "User: $(whoami)"
    echo "Host: $(hostname)"
    echo "Working Directory: $(pwd)"
    echo "Python Path: $(which python)"
    echo "Python Version: $(python --version 2>&1)"
    echo
    echo "ENVIRONMENT VARIABLES"
    echo "===================="
    env | grep -E "(ATHERIS|PYTHON|PATH)" | sort
    echo
    echo "INSTALLED PACKAGES"
    echo "=================="
    pip list | grep -E "(atheris|flask|pytest)" || echo "Package info not available"
    echo
    echo "DISK SPACE"
    echo "=========="
    df -h .
    echo
    echo "MEMORY USAGE"
    echo "============"
    free -h 2>/dev/null || echo "Memory info not available"
    
} > "$RESULTS_DIR/system_info.txt"

print_success "Fuzz test execution completed"
print_status "Results saved to: $RESULTS_DIR/"
print_status "View the log: cat $RESULTS_DIR/atheris_${TEST_NAME}_*.log"

# Clean up background processes
if [ ! -z "$APP_PID" ]; then
    print_status "Cleaning up background processes..."
    kill $APP_PID 2>/dev/null || true
fi

echo
print_status "To reproduce this test:"
print_status "1. Ensure database is running: make db-up"
print_status "2. Ensure app is running: make run"
print_status "3. Run: $FUZZ_CMD"
print_status "4. Or use this script: $0 $TEST_NAME $DURATION"
print_status ""
print_status "Note: All commands use uv for dependency and environment management"

exit 0