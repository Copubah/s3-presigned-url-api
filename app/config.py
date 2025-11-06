import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # AWS Configuration
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID") or ""
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY") or ""
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME") or ""

    # Presigned URL settings
    PRESIGNED_URL_EXPIRATION: int = int(
        os.getenv("PRESIGNED_URL_EXPIRATION", 600)
    )  # 10 minutes

    # File upload settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB
    
    # Security settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Rate limiting settings
    RATE_LIMIT_UPLOAD: int = int(os.getenv("RATE_LIMIT_UPLOAD", "10"))  # per minute
    RATE_LIMIT_DOWNLOAD: int = int(os.getenv("RATE_LIMIT_DOWNLOAD", "30"))  # per minute
    RATE_LIMIT_LIST: int = int(os.getenv("RATE_LIMIT_LIST", "5"))  # per minute
    RATE_LIMIT_DELETE: int = int(os.getenv("RATE_LIMIT_DELETE", "5"))  # per minute
    
    # Logging settings
    AUDIT_LOG_FILE: str = os.getenv("AUDIT_LOG_FILE", "logs/audit.log")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS settings
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # File validation settings
    ENFORCE_FILE_SIZE_ON_UPLOAD: bool = os.getenv("ENFORCE_FILE_SIZE_ON_UPLOAD", "true").lower() == "true"
    SCAN_FILES_FOR_MALWARE: bool = os.getenv("SCAN_FILES_FOR_MALWARE", "false").lower() == "true"

    # Allowed file types and their MIME types
    ALLOWED_FILE_TYPES = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".doc": "application/msword",
        ".docx": (
            "application/vnd.openxmlformats-officedocument." "wordprocessingml.document"
        ),
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".zip": "application/zip",
    }
    
    # Blocked file types (security)
    BLOCKED_FILE_TYPES = {
        ".exe", ".bat", ".cmd", ".com", ".pif", ".scr", ".vbs", ".js", 
        ".jar", ".sh", ".ps1", ".php", ".asp", ".aspx", ".jsp"
    }

    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


settings = Settings()
