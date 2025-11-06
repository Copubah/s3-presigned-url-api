import os
import uuid
from typing import Any, Dict, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

from app.config import settings


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def validate_file_type(self, filename: str) -> Tuple[bool, str]:
        """Validate if the file type is allowed"""
        file_extension = os.path.splitext(filename.lower())[1]

        if file_extension not in settings.ALLOWED_FILE_TYPES:
            allowed_types = list(settings.ALLOWED_FILE_TYPES.keys())
            message = (
                f"File type {file_extension} not allowed. "
                f"Allowed types: {allowed_types}"
            )
            return (False, message)

        return True, settings.ALLOWED_FILE_TYPES[file_extension]

    def generate_unique_key(self, filename: str, prefix: str = "uploads") -> str:
        """Generate a unique S3 key for the file"""
        file_extension = os.path.splitext(filename)[1]
        unique_id = str(uuid.uuid4())
        return f"{prefix}/{unique_id}{file_extension}"

    def generate_upload_url(
        self, filename: str, content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate presigned URL for file upload"""
        try:
            # Validate file type
            is_valid, detected_content_type = self.validate_file_type(filename)
            if not is_valid:
                raise ValueError(detected_content_type)

            # Use provided content type or detected one
            final_content_type = content_type or detected_content_type

            # Generate unique file key
            file_key = self.generate_unique_key(filename)

            # Generate presigned URL for PUT operation
            presigned_url = self.s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": file_key,
                    "ContentType": final_content_type,
                },
                ExpiresIn=settings.PRESIGNED_URL_EXPIRATION,
            )

            return {
                "presigned_url": presigned_url,
                "file_key": file_key,
                "expires_in": settings.PRESIGNED_URL_EXPIRATION,
            }

        except ClientError as e:
            raise Exception(f"AWS S3 error: {str(e)}")

    def generate_download_url(self, file_key: str) -> Dict[str, Any]:
        """Generate presigned URL for file download"""
        try:
            # Check if file exists
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    raise FileNotFoundError("File not found in S3")
                raise e

            # Generate presigned URL for GET operation
            presigned_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_key},
                ExpiresIn=settings.PRESIGNED_URL_EXPIRATION,
            )

            return {
                "presigned_url": presigned_url,
                "file_key": file_key,
                "expires_in": settings.PRESIGNED_URL_EXPIRATION,
            }

        except ClientError as e:
            raise Exception(f"AWS S3 error: {str(e)}")

    def list_files(
        self, prefix: str = "uploads/", max_keys: int = 100
    ) -> Dict[str, Any]:
        """List files in S3 bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix, MaxKeys=max_keys
            )

            files = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    files.append(
                        {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": obj["LastModified"],
                            "etag": obj["ETag"].strip('"'),
                        }
                    )

            return {"files": files, "count": len(files)}

        except ClientError as e:
            raise Exception(f"AWS S3 error: {str(e)}")

    def check_connection(self) -> bool:
        """Check S3 connection health"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False

    def delete_file(self, file_key: str) -> bool:
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError as e:
            raise Exception(f"AWS S3 error: {str(e)}")


# Create a singleton instance
s3_service = S3Service()
