from datetime import datetime
import logging
import os

from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.models import (
    DownloadRequest,
    FileListResponse,
    HealthResponse,
    PresignedUrlResponse,
    UploadRequest,
)
from app.s3_service import s3_service
from app.auth import get_current_user, require_upload, require_download, require_list, require_delete
from app.rate_limiter import check_rate_limit
from app.audit_logger import AuditLogger

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs("logs", exist_ok=True)

app = FastAPI(
    title="S3 Presigned URL API",
    description="Secure API for generating presigned URLs for S3 file uploads and downloads with authentication, rate limiting, and comprehensive auditing",
    version="2.0.0",
    docs_url="/docs" if not settings.is_production() else None,  # Disable docs in production
    redoc_url="/redoc" if not settings.is_production() else None,
)

# Security middleware
if settings.is_production():
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]  # Configure for your domain
    )

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "S3 Presigned URL API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload-url",
            "download": "/download-url",
            "files": "/files",
            "health": "/health",
        },
        "allowed_file_types": list(settings.ALLOWED_FILE_TYPES.keys()),
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    s3_healthy = s3_service.check_connection()

    if not s3_healthy:
        raise HTTPException(status_code=503, detail="S3 connection failed")

    return HealthResponse(
        status="healthy", s3_connection="ok", timestamp=datetime.now()
    )


@app.post("/upload-url", response_model=PresignedUrlResponse)
async def generate_upload_url(
    upload_request: UploadRequest,
    request: Request,
    current_user: dict = Depends(require_upload)
):
    """
    Generate a presigned URL for uploading a file to S3.
    
    Requires authentication and 'upload' permission.
    Subject to rate limiting (10 requests per minute per user).
    """
    user_id = current_user.get("user_id")
    
    # Check rate limits
    await check_rate_limit(request, user_id, "upload")
    
    try:
        # Enhanced file validation
        file_extension = os.path.splitext(upload_request.filename.lower())[1]
        if file_extension in settings.BLOCKED_FILE_TYPES:
            AuditLogger.log_presigned_url_generation(
                user_id, request, "upload", "", upload_request.filename,
                success=False, error_message=f"Blocked file type: {file_extension}"
            )
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} is blocked for security reasons"
            )
        
        result = s3_service.generate_upload_url(
            filename=upload_request.filename, 
            content_type=upload_request.content_type
        )
        
        # Audit log successful URL generation
        AuditLogger.log_presigned_url_generation(
            user_id, request, "upload", result["file_key"], 
            upload_request.filename, result["expires_in"]
        )
        
        logger.info(f"Upload URL generated for user {user_id}, file: {upload_request.filename}")
        return PresignedUrlResponse(**result)

    except ValueError as e:
        AuditLogger.log_presigned_url_generation(
            user_id, request, "upload", "", upload_request.filename,
            success=False, error_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        AuditLogger.log_presigned_url_generation(
            user_id, request, "upload", "", upload_request.filename,
            success=False, error_message=str(e)
        )
        logger.error(f"Upload URL generation failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/download-url", response_model=PresignedUrlResponse)
async def generate_download_url(request: DownloadRequest):
    """
    Generate a presigned URL for downloading a file from S3.

    The client can use this URL to download files directly from S3.
    """
    try:
        result = s3_service.generate_download_url(request.file_key)

        return PresignedUrlResponse(**result)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files", response_model=FileListResponse)
async def list_files(
    prefix: str = Query("uploads/", description="Prefix to filter files"),
    max_keys: int = Query(100, description="Maximum number of files to return"),
):
    """
    List files in the S3 bucket (optional endpoint for file management)
    """
    try:
        result = s3_service.list_files(prefix=prefix, max_keys=max_keys)
        return FileListResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/files/{file_key:path}")
async def delete_file(file_key: str):
    """
    Delete a file from S3 bucket
    """
    try:
        success = s3_service.delete_file(file_key)
        if success:
            return {"message": f"File {file_key} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
