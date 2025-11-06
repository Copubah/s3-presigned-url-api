from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import (
    DownloadRequest,
    FileListResponse,
    HealthResponse,
    PresignedUrlResponse,
    UploadRequest,
)
from app.s3_service import s3_service

app = FastAPI(
    title="S3 Presigned URL API",
    description="API for generating presigned URLs for S3 file uploads and downloads",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
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
async def generate_upload_url(request: UploadRequest):
    """
    Generate a presigned URL for uploading a file to S3.

    The client can use this URL to upload files directly to S3 without
    exposing AWS credentials.
    """
    try:
        result = s3_service.generate_upload_url(
            filename=request.filename, content_type=request.content_type
        )

        return PresignedUrlResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
