# Security Guide

This document outlines the security features and best practices implemented in the S3 Presigned URL API.

## Security Features

### 1. Authentication & Authorization

The API uses JWT-based authentication with role-based permissions:

- Authentication: All endpoints require valid JWT tokens
- Authorization: Users need specific permissions (upload, download, list, delete)
- Token Expiration: Configurable token lifetime (default: 24 hours)

#### Getting Started with Authentication

```python
from app.auth import AuthService

# Create a token for a user
token = AuthService.create_access_token(
    user_id="user123",
    permissions=["upload", "download", "list"]
)

# Use the token in API requests
headers = {"Authorization": f"Bearer {token}"}
```

### 2. Rate Limiting

Prevents abuse with configurable rate limits per user per endpoint:

- Upload URLs: 10 requests per minute (default)
- Download URLs: 30 requests per minute (default)
- File Listing: 5 requests per minute (default)
- File Deletion: 5 requests per minute (default)

Rate limits return HTTP 429 with `Retry-After` header when exceeded.

### 3. Comprehensive Audit Logging

All security events are logged to `logs/audit.log` in JSON format:

- Authentication attempts (success/failure)
- Authorization failures
- Presigned URL generation
- Rate limit violations
- File operations

#### Audit Log Format

```json
{
  "timestamp": "2024-01-01T12:00:00.000000",
  "event_type": "presigned_url_generated",
  "user_id": "user123",
  "success": true,
  "client_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "method": "POST",
  "url": "https://api.example.com/upload-url",
  "details": {
    "operation": "upload",
    "file_key": "uploads/uuid-document.pdf",
    "filename": "document.pdf",
    "expiration_seconds": 600
  }
}
```

### 4. File Type Security

Multiple layers of file type validation:

- Allowed Types: Configurable whitelist of permitted file extensions
- Blocked Types: Hardcoded blacklist of dangerous file types
- MIME Type Validation: Content-Type header enforcement
- Extension Blocking: Prevents executable files (.exe, .bat, .sh, etc.)

#### Blocked File Types

```python
BLOCKED_FILE_TYPES = {
    ".exe", ".bat", ".cmd", ".com", ".pif", ".scr", ".vbs", ".js", 
    ".jar", ".sh", ".ps1", ".php", ".asp", ".aspx", ".jsp"
}
```

### 5. Environment-Based Security

Different security levels based on environment:

- Development: API docs enabled, relaxed CORS
- Production: API docs disabled, strict CORS, trusted host middleware

## Security Configuration

### Environment Variables

```bash
# Security Settings
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_EXPIRATION_HOURS=24
ENVIRONMENT=production

# Rate Limiting
RATE_LIMIT_UPLOAD=10
RATE_LIMIT_DOWNLOAD=30
RATE_LIMIT_LIST=5
RATE_LIMIT_DELETE=5

# CORS (comma-separated domains)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# File Security
ENFORCE_FILE_SIZE_ON_UPLOAD=true
SCAN_FILES_FOR_MALWARE=false
```

### Production Security Checklist

- [ ] Change default JWT secret key
- [ ] Set ENVIRONMENT=production
- [ ] Configure specific CORS origins
- [ ] Enable HTTPS/TLS
- [ ] Set up log monitoring
- [ ] Configure firewall rules
- [ ] Review IAM permissions
- [ ] Enable S3 bucket encryption
- [ ] Set up CloudWatch alarms
- [ ] Implement log rotation

## IAM Permissions

The API requires minimal IAM permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetBucketLocation",
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

## Monitoring & Alerting

### Key Metrics to Monitor

1. Authentication Failures: Unusual patterns may indicate attacks
2. Rate Limit Violations: High rates may indicate abuse
3. File Type Violations: Attempts to upload blocked files
4. Large File Uploads: Monitor for unusual file sizes
5. Geographic Anomalies: Unusual access patterns by location

### Recommended Alerts

- Authentication failure rate > 10/minute
- Rate limit violations > 50/hour
- Blocked file type attempts > 5/hour
- Failed S3 operations > 10/minute

## Security Best Practices

### For Developers

1. Never log sensitive data (tokens, credentials)
2. Validate all inputs before processing
3. Use HTTPS only in production
4. Rotate JWT secrets regularly
5. Monitor audit logs for suspicious activity

### For Operations

1. Regular security updates for dependencies
2. Log monitoring and alerting setup
3. Backup and disaster recovery planning
4. Network security (VPC, security groups)
5. Regular security audits and penetration testing

## Incident Response

### Security Incident Checklist

1. Identify the scope and impact
2. Contain the threat (disable accounts, block IPs)
3. Investigate using audit logs
4. Remediate vulnerabilities
5. Document lessons learned
6. Update security measures

### Emergency Contacts

- Security Team: security@yourdomain.com
- On-call Engineer: +1-xxx-xxx-xxxx
- AWS Support: (if using AWS Support plan)

## Compliance

This API implements security controls that support:

- SOC 2 Type II compliance
- GDPR data protection requirements
- HIPAA security safeguards (with additional controls)
- PCI DSS requirements (for payment-related files)

## Security Updates

This document should be reviewed and updated:

- After security incidents
- When adding new features
- During security audits
- At least quarterly

Last updated: 2024-01-01
Next review: 2024-04-01