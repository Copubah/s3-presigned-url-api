from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class UploadRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"filename": "document.pdf", "content_type": "application/pdf"}
        }
    )

    filename: str = Field(..., description="Name of the file to upload")
    content_type: Optional[str] = Field(None, description="MIME type of the file")


class DownloadRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"file_key": "uploads/document.pdf"}}
    )

    file_key: str = Field(..., description="S3 key of the file to download")


class PresignedUrlResponse(BaseModel):
    presigned_url: str = Field(..., description="The presigned URL")
    expires_in: int = Field(..., description="URL expiration time in seconds")
    file_key: str = Field(..., description="S3 key for the file")
    upload_fields: Optional[dict] = Field(
        None, description="Additional fields for POST uploads"
    )


class FileInfo(BaseModel):
    key: str
    size: int
    last_modified: datetime
    etag: str


class FileListResponse(BaseModel):
    files: List[FileInfo]
    count: int


class HealthResponse(BaseModel):
    status: str
    s3_connection: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
