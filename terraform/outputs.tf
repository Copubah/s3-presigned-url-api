output "s3_bucket_name" {
  description = "Name of the created S3 bucket"
  value       = aws_s3_bucket.file_storage.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the created S3 bucket"
  value       = aws_s3_bucket.file_storage.arn
}

output "iam_user_name" {
  description = "Name of the created IAM user"
  value       = aws_iam_user.api_user.name
}

output "iam_access_key_id" {
  description = "Access key ID for the IAM user"
  value       = aws_iam_access_key.api_user_key.id
  sensitive   = true
}

output "iam_secret_access_key" {
  description = "Secret access key for the IAM user"
  value       = aws_iam_access_key.api_user_key.secret
  sensitive   = true
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.api_logs.name
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = var.deploy_to_ecs ? aws_ecs_cluster.api_cluster[0].name : null
}

output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = var.deploy_to_ecs ? aws_lb.api_alb[0].dns_name : null
}

output "environment_variables" {
  description = "Environment variables for the application"
  value = {
    AWS_REGION                = var.aws_region
    S3_BUCKET_NAME           = aws_s3_bucket.file_storage.bucket
    PRESIGNED_URL_EXPIRATION = "600"
    MAX_FILE_SIZE           = "52428800"
  }
  sensitive = false
}