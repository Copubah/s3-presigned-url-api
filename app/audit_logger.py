"""
Comprehensive audit logging for S3 Presigned URL API
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request
import os

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create audit log handler
audit_handler = logging.FileHandler(
    os.getenv("AUDIT_LOG_FILE", "logs/audit.log")
)
audit_handler.setLevel(logging.INFO)

# Create audit log formatter
audit_formatter = logging.Formatter(
    '%(asctime)s - AUDIT - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)

class AuditLogger:
    """Centralized audit logging for security events"""
    
    @staticmethod
    def log_event(
        event_type: str,
        user_id: str,
        request: Request,
        details: Dict[str, Any] = None,
        success: bool = True,
        error_message: str = None
    ):
        """Log security and operational events"""
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "success": success,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "method": request.method,
            "url": str(request.url),
            "details": details or {}
        }
        
        if error_message:
            audit_entry["error"] = error_message
        
        # Log as JSON for easy parsing
        audit_logger.info(json.dumps(audit_entry))
    
    @staticmethod
    def log_presigned_url_generation(
        user_id: str,
        request: Request,
        operation: str,  # "upload" or "download"
        file_key: str,
        filename: str = None,
        expiration_seconds: int = None,
        success: bool = True,
        error_message: str = None
    ):
        """Log presigned URL generation events"""
        
        details = {
            "operation": operation,
            "file_key": file_key,
            "expiration_seconds": expiration_seconds
        }
        
        if filename:
            details["filename"] = filename
        
        AuditLogger.log_event(
            event_type="presigned_url_generated",
            user_id=user_id,
            request=request,
            details=details,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def log_authentication(
        user_id: str,
        request: Request,
        success: bool = True,
        error_message: str = None
    ):
        """Log authentication attempts"""
        
        AuditLogger.log_event(
            event_type="authentication",
            user_id=user_id,
            request=request,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def log_authorization_failure(
        user_id: str,
        request: Request,
        required_permission: str
    ):
        """Log authorization failures"""
        
        details = {
            "required_permission": required_permission,
            "endpoint": str(request.url.path)
        }
        
        AuditLogger.log_event(
            event_type="authorization_failure",
            user_id=user_id,
            request=request,
            details=details,
            success=False
        )
    
    @staticmethod
    def log_rate_limit_exceeded(
        user_id: str,
        request: Request,
        endpoint: str,
        retry_after: int
    ):
        """Log rate limit violations"""
        
        details = {
            "endpoint": endpoint,
            "retry_after_seconds": retry_after
        }
        
        AuditLogger.log_event(
            event_type="rate_limit_exceeded",
            user_id=user_id,
            request=request,
            details=details,
            success=False
        )
    
    @staticmethod
    def log_file_operation(
        user_id: str,
        request: Request,
        operation: str,  # "list", "delete"
        file_key: str = None,
        file_count: int = None,
        success: bool = True,
        error_message: str = None
    ):
        """Log file operations"""
        
        details = {
            "operation": operation
        }
        
        if file_key:
            details["file_key"] = file_key
        if file_count is not None:
            details["file_count"] = file_count
        
        AuditLogger.log_event(
            event_type="file_operation",
            user_id=user_id,
            request=request,
            details=details,
            success=success,
            error_message=error_message
        )

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)