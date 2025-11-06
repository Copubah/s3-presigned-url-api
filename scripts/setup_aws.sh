#!/bin/bash

# AWS Setup Script for S3 Presigned URL API
# This script helps set up the required AWS resources

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BUCKET_NAME=""
REGION="us-east-1"
IAM_USER_NAME="s3-presigned-api-user"
POLICY_NAME="S3PresignedAPIPolicy"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        echo "Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    
    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI is not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_status "AWS CLI is installed and configured"
}

# Function to get bucket name from user
get_bucket_name() {
    if [ -z "$BUCKET_NAME" ]; then
        echo -n "Enter S3 bucket name: "
        read BUCKET_NAME
    fi
    
    if [ -z "$BUCKET_NAME" ]; then
        print_error "Bucket name cannot be empty"
        exit 1
    fi
    
    print_status "Using bucket name: $BUCKET_NAME"
}

# Function to create S3 bucket
create_s3_bucket() {
    print_status "Creating S3 bucket: $BUCKET_NAME"
    
    if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
        print_warning "Bucket $BUCKET_NAME already exists"
    else
        if [ "$REGION" = "us-east-1" ]; then
            aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION"
        else
            aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" \
                --create-bucket-configuration LocationConstraint="$REGION"
        fi
        print_status "Bucket created successfully"
    fi
}

# Function to configure bucket CORS
configure_cors() {
    print_status "Configuring CORS for bucket: $BUCKET_NAME"
    
    # Create temporary CORS configuration
    cat > /tmp/cors-config.json << EOF
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": ["ETag", "x-amz-meta-custom-header"],
            "MaxAgeSeconds": 3000
        }
    ]
}
EOF
    
    aws s3api put-bucket-cors --bucket "$BUCKET_NAME" --cors-configuration file:///tmp/cors-config.json
    rm /tmp/cors-config.json
    print_status "CORS configuration applied"
}

# Function to create IAM user
create_iam_user() {
    print_status "Creating IAM user: $IAM_USER_NAME"
    
    if aws iam get-user --user-name "$IAM_USER_NAME" 2>/dev/null; then
        print_warning "IAM user $IAM_USER_NAME already exists"
    else
        aws iam create-user --user-name "$IAM_USER_NAME"
        print_status "IAM user created successfully"
    fi
}

# Function to create and attach IAM policy
create_iam_policy() {
    print_status "Creating IAM policy: $POLICY_NAME"
    
    # Create policy document
    cat > /tmp/policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3BucketAccess",
            "Effect": "Allow",
            "Action": [
                "s3:GetBucketLocation",
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::$BUCKET_NAME"
        },
        {
            "Sid": "S3ObjectAccess",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObjectAcl",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF
    
    # Get AWS account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    POLICY_ARN="arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME"
    
    # Check if policy exists
    if aws iam get-policy --policy-arn "$POLICY_ARN" 2>/dev/null; then
        print_warning "Policy $POLICY_NAME already exists"
    else
        aws iam create-policy --policy-name "$POLICY_NAME" --policy-document file:///tmp/policy.json
        print_status "IAM policy created successfully"
    fi
    
    # Attach policy to user
    aws iam attach-user-policy --user-name "$IAM_USER_NAME" --policy-arn "$POLICY_ARN"
    print_status "Policy attached to user"
    
    rm /tmp/policy.json
}

# Function to create access keys
create_access_keys() {
    print_status "Creating access keys for user: $IAM_USER_NAME"
    
    # Check if user already has access keys
    if aws iam list-access-keys --user-name "$IAM_USER_NAME" --query 'AccessKeyMetadata[0].AccessKeyId' --output text 2>/dev/null | grep -q "AKIA"; then
        print_warning "User already has access keys. Skipping creation."
        print_warning "If you need new keys, delete the existing ones first:"
        print_warning "aws iam delete-access-key --user-name $IAM_USER_NAME --access-key-id <ACCESS_KEY_ID>"
        return
    fi
    
    # Create new access keys
    KEYS_OUTPUT=$(aws iam create-access-key --user-name "$IAM_USER_NAME" --output json)
    ACCESS_KEY_ID=$(echo "$KEYS_OUTPUT" | jq -r '.AccessKey.AccessKeyId')
    SECRET_ACCESS_KEY=$(echo "$KEYS_OUTPUT" | jq -r '.AccessKey.SecretAccessKey')
    
    print_status "Access keys created successfully!"
    echo
    echo "=== IMPORTANT: Save these credentials securely ==="
    echo "AWS_ACCESS_KEY_ID=$ACCESS_KEY_ID"
    echo "AWS_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY"
    echo "AWS_REGION=$REGION"
    echo "S3_BUCKET_NAME=$BUCKET_NAME"
    echo "=================================================="
    echo
    print_warning "These credentials will not be shown again!"
    print_warning "Add them to your .env file"
}

# Function to test the setup
test_setup() {
    print_status "Testing the setup..."
    
    # Test bucket access
    if aws s3 ls "s3://$BUCKET_NAME" >/dev/null 2>&1; then
        print_status "✓ Bucket access test passed"
    else
        print_error "✗ Bucket access test failed"
    fi
    
    # Test CORS configuration
    if aws s3api get-bucket-cors --bucket "$BUCKET_NAME" >/dev/null 2>&1; then
        print_status "✓ CORS configuration test passed"
    else
        print_error "✗ CORS configuration test failed"
    fi
}

# Main execution
main() {
    echo "=== AWS Setup for S3 Presigned URL API ==="
    echo
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --bucket-name)
                BUCKET_NAME="$2"
                shift 2
                ;;
            --region)
                REGION="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [--bucket-name BUCKET_NAME] [--region REGION]"
                echo "  --bucket-name: S3 bucket name (will prompt if not provided)"
                echo "  --region: AWS region (default: us-east-1)"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    check_aws_cli
    get_bucket_name
    create_s3_bucket
    configure_cors
    create_iam_user
    create_iam_policy
    create_access_keys
    test_setup
    
    echo
    print_status "Setup completed successfully!"
    print_status "You can now run your FastAPI application with the generated credentials."
}

# Run main function
main "$@"