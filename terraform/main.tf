terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# S3 Bucket for file storage
resource "aws_s3_bucket" "file_storage" {
  bucket = var.bucket_name

  tags = {
    Name        = "S3 Presigned API Storage"
    Environment = var.environment
    Project     = "s3-presigned-api"
  }
}

# S3 Bucket versioning
resource "aws_s3_bucket_versioning" "file_storage_versioning" {
  bucket = aws_s3_bucket.file_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "file_storage_encryption" {
  bucket = aws_s3_bucket.file_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket public access block
resource "aws_s3_bucket_public_access_block" "file_storage_pab" {
  bucket = aws_s3_bucket.file_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket CORS configuration
resource "aws_s3_bucket_cors_configuration" "file_storage_cors" {
  bucket = aws_s3_bucket.file_storage.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = var.cors_allowed_origins
    expose_headers  = ["ETag", "x-amz-meta-custom-header"]
    max_age_seconds = 3000
  }
}

# S3 Bucket lifecycle configuration
resource "aws_s3_bucket_lifecycle_configuration" "file_storage_lifecycle" {
  bucket = aws_s3_bucket.file_storage.id

  rule {
    id     = "cleanup_old_files"
    status = "Enabled"

    expiration {
      days = var.file_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# IAM User for the application
resource "aws_iam_user" "api_user" {
  name = "${var.project_name}-api-user"
  path = "/"

  tags = {
    Name        = "S3 Presigned API User"
    Environment = var.environment
    Project     = "s3-presigned-api"
  }
}

# IAM Policy for S3 access
resource "aws_iam_policy" "s3_access_policy" {
  name        = "${var.project_name}-s3-access"
  description = "Policy for S3 presigned URL API access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3BucketAccess"
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.file_storage.arn
      },
      {
        Sid    = "S3ObjectAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObjectAcl",
          "s3:PutObjectAcl"
        ]
        Resource = "${aws_s3_bucket.file_storage.arn}/*"
      }
    ]
  })
}

# Attach policy to user
resource "aws_iam_user_policy_attachment" "api_user_policy" {
  user       = aws_iam_user.api_user.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}

# Create access keys for the user
resource "aws_iam_access_key" "api_user_key" {
  user = aws_iam_user.api_user.name
}

# CloudWatch Log Group for application logs
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/ecs/${var.project_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "S3 Presigned API Logs"
    Environment = var.environment
    Project     = "s3-presigned-api"
  }
}

# ECS Cluster (optional - for container deployment)
resource "aws_ecs_cluster" "api_cluster" {
  count = var.deploy_to_ecs ? 1 : 0
  name  = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "S3 Presigned API Cluster"
    Environment = var.environment
    Project     = "s3-presigned-api"
  }
}

# Application Load Balancer (optional)
resource "aws_lb" "api_alb" {
  count              = var.deploy_to_ecs ? 1 : 0
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg[0].id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "production"

  tags = {
    Name        = "S3 Presigned API ALB"
    Environment = var.environment
    Project     = "s3-presigned-api"
  }
}

# Security Group for ALB
resource "aws_security_group" "alb_sg" {
  count       = var.deploy_to_ecs ? 1 : 0
  name_prefix = "${var.project_name}-alb-"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "S3 Presigned API ALB Security Group"
    Environment = var.environment
    Project     = "s3-presigned-api"
  }
}

# Security Group for ECS tasks
resource "aws_security_group" "ecs_sg" {
  count       = var.deploy_to_ecs ? 1 : 0
  name_prefix = "${var.project_name}-ecs-"
  vpc_id      = var.vpc_id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg[0].id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "S3 Presigned API ECS Security Group"
    Environment = var.environment
    Project     = "s3-presigned-api"
  }
}