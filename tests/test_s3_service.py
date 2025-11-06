from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from app.config import settings
from app.s3_service import S3Service


class TestS3Service:

    @patch("boto3.client")
    def test_init(self, mock_boto_client):
        """Test S3Service initialization"""
        S3Service()
        mock_boto_client.assert_called_once_with(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

    def test_validate_file_type_valid(self):
        """Test file type validation with valid file"""
        service = S3Service()
        is_valid, content_type = service.validate_file_type("test.pdf")
        assert is_valid is True
        assert content_type == "application/pdf"

    def test_validate_file_type_invalid(self):
        """Test file type validation with invalid file"""
        service = S3Service()
        is_valid, error_msg = service.validate_file_type("malware.exe")
        assert is_valid is False
        assert "not allowed" in error_msg

    def test_generate_unique_key(self):
        """Test unique key generation"""
        service = S3Service()
        key1 = service.generate_unique_key("test.pdf")
        key2 = service.generate_unique_key("test.pdf")

        assert key1 != key2  # Should be unique
        assert key1.startswith("uploads/")
        assert key1.endswith(".pdf")

    @patch("boto3.client")
    def test_generate_upload_url_success(self, mock_boto_client):
        """Test successful upload URL generation"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.generate_presigned_url.return_value = (
            "https://s3.amazonaws.com/test-url"
        )

        service = S3Service()
        result = service.generate_upload_url("test.pdf")

        assert "presigned_url" in result
        assert "file_key" in result
        assert "expires_in" in result
        assert result["expires_in"] == settings.PRESIGNED_URL_EXPIRATION

    @patch("boto3.client")
    def test_generate_upload_url_invalid_file(self, mock_boto_client):
        """Test upload URL generation with invalid file type"""
        service = S3Service()

        with pytest.raises(ValueError):
            service.generate_upload_url("malware.exe")

    @patch("boto3.client")
    def test_generate_download_url_success(self, mock_boto_client):
        """Test successful download URL generation"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_object.return_value = {}  # File exists
        mock_s3.generate_presigned_url.return_value = (
            "https://s3.amazonaws.com/download-url"
        )

        service = S3Service()
        result = service.generate_download_url("uploads/test.pdf")

        assert "presigned_url" in result
        assert result["file_key"] == "uploads/test.pdf"

    @patch("boto3.client")
    def test_generate_download_url_file_not_found(self, mock_boto_client):
        """Test download URL generation for non-existent file"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        # Simulate file not found
        error_response = {"Error": {"Code": "404"}}
        mock_s3.head_object.side_effect = ClientError(error_response, "head_object")

        service = S3Service()

        with pytest.raises(FileNotFoundError):
            service.generate_download_url("uploads/nonexistent.pdf")

    @patch("boto3.client")
    def test_list_files_success(self, mock_boto_client):
        """Test successful file listing"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        mock_response = {
            "Contents": [
                {
                    "Key": "uploads/test.pdf",
                    "Size": 1024,
                    "LastModified": "2024-01-01T12:00:00",
                    "ETag": '"abc123"',
                }
            ]
        }
        mock_s3.list_objects_v2.return_value = mock_response

        service = S3Service()
        result = service.list_files()

        assert result["count"] == 1
        assert len(result["files"]) == 1
        assert result["files"][0]["key"] == "uploads/test.pdf"

    @patch("boto3.client")
    def test_list_files_empty(self, mock_boto_client):
        """Test file listing with no files"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.list_objects_v2.return_value = {}  # No Contents key

        service = S3Service()
        result = service.list_files()

        assert result["count"] == 0
        assert result["files"] == []

    @patch("boto3.client")
    def test_check_connection_success(self, mock_boto_client):
        """Test successful connection check"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}

        service = S3Service()
        result = service.check_connection()

        assert result is True

    @patch("boto3.client")
    def test_check_connection_failure(self, mock_boto_client):
        """Test connection check failure"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.side_effect = ClientError({}, "head_bucket")

        service = S3Service()
        result = service.check_connection()

        assert result is False

    @patch("boto3.client")
    def test_delete_file_success(self, mock_boto_client):
        """Test successful file deletion"""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.delete_object.return_value = {}

        service = S3Service()
        result = service.delete_file("uploads/test.pdf")

        assert result is True
        mock_s3.delete_object.assert_called_once_with(
            Bucket=settings.S3_BUCKET_NAME, Key="uploads/test.pdf"
        )
