#!/bin/bash

# Full Automation Script for S3 Presigned URL API
# This script automates the entire deployment process

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
    echo -e "${BLUE}[AUTOMATION]${NC} $1"
}

# Configuration
ENVIRONMENT="dev"
PROJECT_NAME="s3-presigned-api"
BUCKET_NAME=""
AWS_REGION="us-east-1"
DEPLOYMENT_TYPE="docker"  # docker, k8s, or terraform
SKIP_TESTS=false
AUTO_APPROVE=false

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --environment ENV     Environment (dev, staging, prod) [default: dev]"
    echo "  --bucket-name NAME    S3 bucket name (required)"
    echo "  --region REGION       AWS region [default: us-east-1]"
    echo "  --deployment TYPE     Deployment type (docker, k8s, terraform) [default: docker]"
    echo "  --skip-tests         Skip running tests"
    echo "  --auto-approve       Auto-approve all prompts"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --bucket-name my-api-bucket --environment prod --deployment k8s"
    echo "  $0 --bucket-name test-bucket --skip-tests --auto-approve"
}

# Function to parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --bucket-name)
                BUCKET_NAME="$2"
                shift 2
                ;;
            --region)
                AWS_REGION="$2"
                shift 2
                ;;
            --deployment)
                DEPLOYMENT_TYPE="$2"
                shift 2
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --auto-approve)
                AUTO_APPROVE=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    if [ -z "$BUCKET_NAME" ]; then
        print_error "Bucket name is required. Use --bucket-name option."
        show_usage
        exit 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check required tools
    local tools=("aws" "docker" "python3" "pip")
    
    if [ "$DEPLOYMENT_TYPE" = "k8s" ]; then
        tools+=("kubectl")
    fi
    
    if [ "$DEPLOYMENT_TYPE" = "terraform" ]; then
        tools+=("terraform")
    fi
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            print_error "$tool is not installed"
            exit 1
        fi
        print_status "✓ $tool is installed"
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured"
        exit 1
    fi
    print_status "✓ AWS credentials configured"
}

# Function to setup environment
setup_environment() {
    print_header "Setting Up Environment"
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        cp .env.example .env
        
        # Update .env with provided values
        sed -i "s/AWS_REGION=.*/AWS_REGION=$AWS_REGION/" .env
        sed -i "s/S3_BUCKET_NAME=.*/S3_BUCKET_NAME=$BUCKET_NAME/" .env
        
        print_warning ".env file created. You may need to update AWS credentials manually."
    fi
}

# Function to run tests
run_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        print_warning "Skipping tests as requested"
        return
    fi
    
    print_header "Running Tests"
    
    if [ -f "scripts/run_tests.sh" ]; then
        bash scripts/run_tests.sh
    else
        print_warning "Test script not found, running basic tests..."
        python -m pytest tests/ -v
    fi
}

# Function to setup AWS resources
setup_aws_resources() {
    print_header "Setting Up AWS Resources"
    
    if [ "$DEPLOYMENT_TYPE" = "terraform" ]; then
        setup_terraform
    else
        # Use the AWS setup script
        if [ -f "scripts/setup_aws.sh" ]; then
            bash scripts/setup_aws.sh --bucket-name "$BUCKET_NAME" --region "$AWS_REGION"
        else
            print_error "AWS setup script not found"
            exit 1
        fi
    fi
}

# Function to setup Terraform
setup_terraform() {
    print_status "Setting up infrastructure with Terraform..."
    
    cd terraform
    
    # Initialize Terraform
    terraform init
    
    # Create terraform.tfvars
    cat > terraform.tfvars << EOF
aws_region = "$AWS_REGION"
environment = "$ENVIRONMENT"
project_name = "$PROJECT_NAME"
bucket_name = "$BUCKET_NAME"
cors_allowed_origins = ["*"]
file_retention_days = 90
log_retention_days = 30
deploy_to_ecs = false
EOF
    
    # Plan and apply
    terraform plan
    
    if [ "$AUTO_APPROVE" = true ]; then
        terraform apply -auto-approve
    else
        terraform apply
    fi
    
    # Extract outputs
    AWS_ACCESS_KEY_ID=$(terraform output -raw iam_access_key_id)
    AWS_SECRET_ACCESS_KEY=$(terraform output -raw iam_secret_access_key)
    
    cd ..
    
    # Update .env file
    sed -i "s/AWS_ACCESS_KEY_ID=.*/AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID/" .env
    sed -i "s/AWS_SECRET_ACCESS_KEY=.*/AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY/" .env
}

# Function to deploy application
deploy_application() {
    print_header "Deploying Application"
    
    case $DEPLOYMENT_TYPE in
        docker)
            deploy_docker
            ;;
        k8s)
            deploy_kubernetes
            ;;
        terraform)
            print_status "Application infrastructure deployed with Terraform"
            ;;
        *)
            print_error "Unknown deployment type: $DEPLOYMENT_TYPE"
            exit 1
            ;;
    esac
}

# Function to deploy with Docker
deploy_docker() {
    print_status "Deploying with Docker..."
    
    if [ -f "scripts/deploy.sh" ]; then
        bash scripts/deploy.sh
    else
        # Basic Docker deployment
        docker build -t "$PROJECT_NAME:latest" .
        
        # Stop existing container
        docker stop "$PROJECT_NAME-container" 2>/dev/null || true
        docker rm "$PROJECT_NAME-container" 2>/dev/null || true
        
        # Start new container
        docker run -d \
            --name "$PROJECT_NAME-container" \
            --env-file .env \
            -p 8000:8000 \
            --restart unless-stopped \
            "$PROJECT_NAME:latest"
    fi
}

# Function to deploy to Kubernetes
deploy_kubernetes() {
    print_status "Deploying to Kubernetes..."
    
    # Create namespace
    kubectl apply -f k8s/namespace.yaml
    
    # Create ConfigMap
    kubectl apply -f k8s/configmap.yaml
    
    # Update ConfigMap with bucket name
    kubectl patch configmap s3-presigned-api-config -n s3-presigned-api \
        --patch "{\"data\":{\"S3_BUCKET_NAME\":\"$BUCKET_NAME\"}}"
    
    # Create Secret (you'll need to update this with actual credentials)
    print_warning "Please update k8s/secret.yaml with your AWS credentials before proceeding"
    if [ "$AUTO_APPROVE" = false ]; then
        read -p "Press Enter to continue after updating the secret..."
    fi
    kubectl apply -f k8s/secret.yaml
    
    # Deploy application
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/hpa.yaml
    
    # Optionally deploy ingress
    if [ "$ENVIRONMENT" != "dev" ]; then
        kubectl apply -f k8s/ingress.yaml
    fi
    
    # Wait for deployment
    kubectl rollout status deployment/s3-presigned-api -n s3-presigned-api
}

# Function to run post-deployment tests
run_post_deployment_tests() {
    print_header "Running Post-Deployment Tests"
    
    # Wait for application to be ready
    sleep 10
    
    # Determine the application URL
    case $DEPLOYMENT_TYPE in
        docker)
            APP_URL="http://localhost:8000"
            ;;
        k8s)
            if [ "$ENVIRONMENT" = "dev" ]; then
                # Port forward for testing
                kubectl port-forward service/s3-presigned-api-service 8000:80 -n s3-presigned-api &
                PORT_FORWARD_PID=$!
                sleep 5
                APP_URL="http://localhost:8000"
            else
                APP_URL="https://api.yourdomain.com"  # Update with your domain
            fi
            ;;
        terraform)
            APP_URL="http://localhost:8000"  # Adjust based on your Terraform setup
            ;;
    esac
    
    # Test health endpoint
    print_status "Testing health endpoint..."
    if curl -f -s "$APP_URL/health" > /dev/null; then
        print_status "✓ Health check passed"
    else
        print_error "✗ Health check failed"
        return 1
    fi
    
    # Test root endpoint
    print_status "Testing root endpoint..."
    if curl -f -s "$APP_URL/" > /dev/null; then
        print_status "✓ Root endpoint test passed"
    else
        print_error "✗ Root endpoint test failed"
        return 1
    fi
    
    # Clean up port forward if used
    if [ -n "$PORT_FORWARD_PID" ]; then
        kill $PORT_FORWARD_PID 2>/dev/null || true
    fi
    
    print_status "All post-deployment tests passed!"
}

# Function to show deployment summary
show_deployment_summary() {
    print_header "Deployment Summary"
    echo
    echo "🚀 Project: $PROJECT_NAME"
    echo "🌍 Environment: $ENVIRONMENT"
    echo "🪣 S3 Bucket: $BUCKET_NAME"
    echo "🌐 AWS Region: $AWS_REGION"
    echo "📦 Deployment Type: $DEPLOYMENT_TYPE"
    echo
    
    case $DEPLOYMENT_TYPE in
        docker)
            echo "🐳 Docker Container: $PROJECT_NAME-container"
            echo "🌐 URL: http://localhost:8000"
            echo "📚 Docs: http://localhost:8000/docs"
            echo
            echo "Useful commands:"
            echo "  View logs: docker logs $PROJECT_NAME-container -f"
            echo "  Stop app:  docker stop $PROJECT_NAME-container"
            echo "  Restart:   docker restart $PROJECT_NAME-container"
            ;;
        k8s)
            echo "☸️  Kubernetes Namespace: s3-presigned-api"
            echo "🌐 URL: (depends on ingress configuration)"
            echo
            echo "Useful commands:"
            echo "  View pods: kubectl get pods -n s3-presigned-api"
            echo "  View logs: kubectl logs -f deployment/s3-presigned-api -n s3-presigned-api"
            echo "  Port forward: kubectl port-forward service/s3-presigned-api-service 8000:80 -n s3-presigned-api"
            ;;
        terraform)
            echo "🏗️  Infrastructure: Managed by Terraform"
            echo "📁 Terraform state: terraform/"
            echo
            echo "Useful commands:"
            echo "  View outputs: cd terraform && terraform output"
            echo "  Destroy: cd terraform && terraform destroy"
            ;;
    esac
    echo
}

# Main execution
main() {
    echo "=== Full Automation for S3 Presigned URL API ==="
    echo
    
    parse_args "$@"
    check_prerequisites
    setup_environment
    run_tests
    setup_aws_resources
    deploy_application
    run_post_deployment_tests
    show_deployment_summary
    
    print_status "🎉 Automation completed successfully!"
}

# Run main function with all arguments
main "$@"