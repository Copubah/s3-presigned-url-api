# Complete Automation Guide

This project includes comprehensive automation for deployment, testing, and infrastructure management. Here's everything you need to know about the automation capabilities.

## Quick Start - Full Automation

The easiest way to get everything up and running:

```bash
# One-command deployment
./scripts/full_automation.sh --bucket-name my-api-bucket --environment prod --deployment docker

# With Kubernetes
./scripts/full_automation.sh --bucket-name my-api-bucket --deployment k8s --auto-approve

# With Terraform (full infrastructure)
./scripts/full_automation.sh --bucket-name my-api-bucket --deployment terraform --environment prod
```

## Automation Components

### 1. Infrastructure as Code (Terraform)
Directory: `terraform/`

Features:
- Complete AWS infrastructure setup
- S3 bucket with proper configuration
- IAM user and policies
- CloudWatch logging
- Optional ECS deployment
- Load balancer setup

**Usage**:
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

### 2. Kubernetes Deployment
Directory: `k8s/`

Features:
- Production-ready Kubernetes manifests
- Horizontal Pod Autoscaling (HPA)
- Ingress with SSL termination
- ConfigMaps and Secrets management
- Health checks and probes
- Security contexts

Usage:
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Or use the automation script
./scripts/full_automation.sh --deployment k8s --bucket-name your-bucket
```

### 3. Docker Deployment
Files: `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`

Features:
- Multi-stage Docker builds
- Production-ready compose setup
- Nginx reverse proxy with rate limiting
- Monitoring with Prometheus & Grafana
- Health checks and auto-restart

Usage:
```bash
# Development
docker-compose up -d

# Production with monitoring
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Monitoring & Observability
Directory: `monitoring/`

Features:
- Prometheus metrics collection
- Grafana dashboards
- Alert rules for critical issues
- Application performance monitoring
- Infrastructure monitoring

Included Alerts:
- API downtime
- High error rates
- Slow response times
- S3 connection failures

## Automation Scripts

### Full Automation Script
File: `scripts/full_automation.sh`

This is the master script that orchestrates everything:

```bash
# Full deployment with all options
./scripts/full_automation.sh \
  --bucket-name my-production-bucket \
  --environment prod \
  --region us-west-2 \
  --deployment terraform \
  --auto-approve
```

What it does:
1. Checks prerequisites
2. Sets up environment
3. Runs tests
4. Creates AWS resources
5. Deploys application
6. Runs post-deployment tests
7. Shows deployment summary

### AWS Setup Script
File: `scripts/setup_aws.sh`

Automated AWS resource creation:

```bash
./scripts/setup_aws.sh --bucket-name my-bucket --region us-east-1
```

Creates:
- S3 bucket with proper configuration
- IAM user with minimal permissions
- CORS policy
- Access keys

### Test Runner Script
File: `scripts/run_tests.sh`

Comprehensive testing automation:

```bash
# Run all tests
./scripts/run_tests.sh

# Only linting
./scripts/run_tests.sh --lint-only

# Only type checking
./scripts/run_tests.sh --type-check-only
```

Includes:
- Unit tests with coverage
- Code linting (flake8)
- Code formatting (black)
- Import sorting (isort)
- Type checking (mypy)

### Deployment Script
File: `scripts/deploy.sh`

Docker deployment automation:

```bash
# Deploy with Docker
./scripts/deploy.sh

# Deploy with Docker Compose
./scripts/deploy.sh --docker-compose

# Show logs after deployment
./scripts/deploy.sh --logs
```

## Deployment Workflows

### 1. Development Workflow
```bash
# Quick development setup
git clone <repository>
cd s3-presigned-api
./scripts/full_automation.sh --bucket-name dev-bucket --environment dev
```

### 2. Staging Workflow
```bash
# Staging deployment with Kubernetes
./scripts/full_automation.sh \
  --bucket-name staging-bucket \
  --environment staging \
  --deployment k8s
```

### 3. Production Workflow
```bash
# Production deployment with full infrastructure
./scripts/full_automation.sh \
  --bucket-name prod-bucket \
  --environment prod \
  --deployment terraform \
  --auto-approve
```

## Configuration Options

### Environment Variables
All automation scripts respect these environment variables:

```bash
# AWS Configuration
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Application Configuration
export S3_BUCKET_NAME=your-bucket
export PRESIGNED_URL_EXPIRATION=600
export MAX_FILE_SIZE=52428800

# Deployment Configuration
export ENVIRONMENT=prod
export DEPLOYMENT_TYPE=docker
```

### Terraform Variables
File: `terraform/terraform.tfvars`

```hcl
aws_region = "us-east-1"
environment = "prod"
bucket_name = "my-production-bucket"
cors_allowed_origins = ["https://myapp.com"]
file_retention_days = 90
deploy_to_ecs = true
```

### Kubernetes Configuration
Update these files for your environment:
- `k8s/configmap.yaml` - Application configuration
- `k8s/secret.yaml` - AWS credentials
- `k8s/ingress.yaml` - Domain and SSL settings

## Monitoring & Alerts

### Prometheus Metrics
Access at: `http://localhost:9090`

Custom Metrics:
- `http_requests_total` - Request count by status
- `http_request_duration_seconds` - Response time histogram
- `s3_connection_failures_total` - S3 connection issues
- `presigned_url_generation_total` - URL generation count

### Grafana Dashboards
Access at: `http://localhost:3000` (admin/admin123)

Dashboards:
- API Performance Overview
- Error Rate Monitoring
- S3 Operations Metrics
- Infrastructure Health

### Alert Rules
File: `monitoring/alert_rules.yml`

Alerts:
- API Down (critical)
- High Error Rate (warning)
- High Response Time (warning)
- S3 Connection Failure (critical)

## Security Automation

### Code Security Scanning
Manual security checks available:
- Bandit: Python security linter
- Safety: Dependency vulnerability scanner
- Docker: Container security scanning

### Infrastructure Security
- IAM policies with minimal permissions
- S3 bucket security (encryption, public access blocked)
- Network security groups
- SSL/TLS termination

## Performance Optimization

### Automated Scaling
- Kubernetes HPA: CPU/Memory based scaling
- Docker Swarm: Service replication
- ECS: Auto Scaling Groups

### Caching & CDN
- Nginx reverse proxy with caching
- CloudFront integration (via Terraform)
- Application-level caching

## Troubleshooting Automation

### Common Issues

1. AWS Credentials:
```bash
# Check credentials
aws sts get-caller-identity

# Configure if needed
aws configure
```

2. Docker Issues:
```bash
# Check Docker daemon
docker info

# Clean up
docker system prune -a
```

3. Kubernetes Issues:
```bash
# Check cluster connection
kubectl cluster-info

# Check pod status
kubectl get pods -n s3-presigned-api
```

### Debug Mode
Enable debug output in scripts:
```bash
export DEBUG=true
./scripts/full_automation.sh --bucket-name test-bucket
```

## Advanced Automation

### Custom Deployment Workflows
Create custom deployment scripts by combining automation tools:

```bash
#!/bin/bash
# Custom deployment workflow

# Run tests
./scripts/run_tests.sh

# Deploy infrastructure
cd terraform && terraform apply -auto-approve

# Deploy application
./scripts/deploy.sh --docker-compose

# Run integration tests
python examples/client_examples.py
```

### Multi-Environment Management
Use environment-specific configurations:

```bash
# Development
./scripts/full_automation.sh --environment dev --bucket-name dev-bucket

# Staging
./scripts/full_automation.sh --environment staging --bucket-name staging-bucket

# Production
./scripts/full_automation.sh --environment prod --bucket-name prod-bucket
```

This automation setup provides a complete, production-ready deployment system that can scale from development to enterprise production environments.