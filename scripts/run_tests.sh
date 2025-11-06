#!/bin/bash

# Test runner script for S3 Presigned URL API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if pytest is installed
check_pytest() {
    if ! python -c "import pytest" 2>/dev/null; then
        print_warning "pytest not found. Installing..."
        pip install pytest pytest-cov pytest-asyncio httpx
    fi
}

# Run tests with coverage
run_tests() {
    print_status "Running tests with coverage..."
    
    python -m pytest tests/ \
        --cov=app \
        --cov=main \
        --cov-report=html \
        --cov-report=term-missing \
        --verbose \
        "$@"
}

# Run linting
run_linting() {
    print_status "Running code linting..."
    
    # Install linting tools if not present
    if ! python -c "import flake8" 2>/dev/null; then
        print_warning "flake8 not found. Installing..."
        pip install flake8 black isort
    fi
    
    # Run black formatter check
    print_status "Checking code formatting with black..."
    python -m black --check --diff app/ main.py tests/ || {
        print_warning "Code formatting issues found. Run 'black app/ main.py tests/' to fix."
    }
    
    # Run isort import sorting check
    print_status "Checking import sorting with isort..."
    python -m isort --check-only --diff app/ main.py tests/ || {
        print_warning "Import sorting issues found. Run 'isort app/ main.py tests/' to fix."
    }
    
    # Run flake8 linting
    print_status "Running flake8 linting..."
    python -m flake8 app/ main.py tests/ --max-line-length=88 --extend-ignore=E203,W503
}

# Run type checking
run_type_checking() {
    print_status "Running type checking with mypy..."
    
    if ! python -c "import mypy" 2>/dev/null; then
        print_warning "mypy not found. Installing..."
        pip install mypy types-requests
    fi
    
    python -m mypy app/ main.py --ignore-missing-imports
}

# Generate test report
generate_report() {
    print_status "Test results:"
    
    if [ -d "htmlcov" ]; then
        print_status "Coverage report generated in htmlcov/index.html"
        
        # Calculate coverage percentage
        COVERAGE=$(python -c "
import re
with open('htmlcov/index.html', 'r') as f:
    content = f.read()
    match = re.search(r'pc_cov.*?(\d+)%', content)
    if match:
        print(match.group(1))
    else:
        print('Unknown')
")
        print_status "Total coverage: ${COVERAGE}%"
    fi
}

# Main execution
main() {
    echo "=== Running Tests for S3 Presigned URL API ==="
    echo
    
    # Parse command line arguments
    LINT_ONLY=false
    TYPE_CHECK_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --lint-only)
                LINT_ONLY=true
                shift
                ;;
            --type-check-only)
                TYPE_CHECK_ONLY=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS] [PYTEST_ARGS]"
                echo "Options:"
                echo "  --lint-only       Run only linting checks"
                echo "  --type-check-only Run only type checking"
                echo "  --help           Show this help message"
                echo ""
                echo "Any additional arguments are passed to pytest"
                exit 0
                ;;
            *)
                break
                ;;
        esac
    done
    
    if [ "$LINT_ONLY" = true ]; then
        run_linting
        exit 0
    fi
    
    if [ "$TYPE_CHECK_ONLY" = true ]; then
        run_type_checking
        exit 0
    fi
    
    # Run all checks
    check_pytest
    run_linting
    run_type_checking
    run_tests "$@"
    generate_report
    
    print_status "All tests completed!"
}

# Run main function with all arguments
main "$@"