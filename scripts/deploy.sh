#!/bin/bash

# Deployment script for S3 Presigned URL API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}[DEPLOY]${NC} $1"
}

# Configuration
APP_NAME="s3-presigned-api"
DOCKER_IMAGE="$APP_NAME:latest"
CONTAINER_NAME="$APP_NAME-container"
PORT="8000"
ENV_FILE=".env"

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        print_error ".env file not found. Please create it from .env.example"
        exit 1
    fi
    
    # Check if required environment variables are set
    source "$ENV_FILE"
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$S3_BUCKET_NAME" ]; then
        print_error "Required environment variables are not set in $ENV_FILE"
        print_error "Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME"
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Function to run tests before deployment
run_tests() {
    print_status "Running tests before deployment..."
    
    if [ -f "scripts/run_tests.sh" ]; then
        bash scripts/run_tests.sh --lint-only
    else
        print_warning "Test script not found, skipping tests"
    fi
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image: $DOCKER_IMAGE"
    
    docker build -t "$DOCKER_IMAGE" .
    
    print_status "Docker image built successfully"
}

# Function to stop existing container
stop_existing_container() {
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        print_status "Stopping existing container: $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
    fi
}

# Function to deploy with Docker
deploy_docker() {
    print_header "Deploying with Docker..."
    
    stop_existing_container
    
    print_status "Starting new container: $CONTAINER_NAME"
    
    docker run -d \
        --name "$CONTAINER_NAME" \
        --env-file "$ENV_FILE" \
        -p "$PORT:8000" \
        --restart unless-stopped \
        "$DOCKER_IMAGE"
    
    # Wait for container to start
    sleep 5
    
    # Check if container is running
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        print_status "Container started successfully"
        print_status "API is available at: http://localhost:$PORT"
        print_status "API documentation: http://localhost:$PORT/docs"
    else
        print_error "Container failed to start"
        print_error "Container logs:"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi
}

# Function to deploy with Docker Compose
deploy_docker_compose() {
    print_header "Deploying with Docker Compose..."
    
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found"
        exit 1
    fi
    
    # Stop existing services
    docker-compose down
    
    # Build and start services
    docker-compose up -d --build
    
    # Wait for services to start
    sleep 10
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        print_status "Services started successfully"
        print_status "API is available at: http://localhost:$PORT"
    else
        print_error "Services failed to start"
        print_error "Service logs:"
        docker-compose logs
        exit 1
    fi
}

# Function to test deployment
test_deployment() {
    print_status "Testing deployment..."
    
    # Wait a bit more for the service to be fully ready
    sleep 5
    
    # Test health endpoint
    if curl -f -s "http://localhost:$PORT/health" > /dev/null; then
        print_status "✓ Health check passed"
    else
        print_error "✗ Health check failed"
        return 1
    fi
    
    # Test root endpoint
    if curl -f -s "http://localhost:$PORT/" > /dev/null; then
        print_status "✓ Root endpoint test passed"
    else
        print_error "✗ Root endpoint test failed"
        return 1
    fi
    
    print_status "Deployment tests passed!"
}

# Function to show deployment info
show_deployment_info() {
    print_header "Deployment Information"
    echo
    echo "🚀 Application: $APP_NAME"
    echo "🐳 Container: $CONTAINER_NAME"
    echo "🌐 URL: http://localhost:$PORT"
    echo "📚 Docs: http://localhost:$PORT/docs"
    echo "🔍 ReDoc: http://localhost:$PORT/redoc"
    echo
    echo "Useful commands:"
    echo "  View logs: docker logs $CONTAINER_NAME -f"
    echo "  Stop app:  docker stop $CONTAINER_NAME"
    echo "  Restart:   docker restart $CONTAINER_NAME"
    echo
}

# Function to show logs
show_logs() {
    print_status "Showing application logs..."
    docker logs "$CONTAINER_NAME" -f
}

# Main execution
main() {
    echo "=== S3 Presigned URL API Deployment ==="
    echo
    
    # Parse command line arguments
    DEPLOYMENT_METHOD="docker"
    SKIP_TESTS=false
    SHOW_LOGS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --docker-compose)
                DEPLOYMENT_METHOD="docker-compose"
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --logs)
                SHOW_LOGS=true
                shift
                ;;
            --port)
                PORT="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --docker-compose  Use Docker Compose for deployment"
                echo "  --skip-tests      Skip running tests before deployment"
                echo "  --logs           Show logs after deployment"
                echo "  --port PORT      Set the port (default: 8000)"
                echo "  --help           Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    check_prerequisites
    
    if [ "$SKIP_TESTS" = false ]; then
        run_tests
    fi
    
    if [ "$DEPLOYMENT_METHOD" = "docker-compose" ]; then
        deploy_docker_compose
    else
        build_image
        deploy_docker
    fi
    
    test_deployment
    show_deployment_info
    
    if [ "$SHOW_LOGS" = true ]; then
        show_logs
    fi
}

# Run main function with all arguments
main "$@"