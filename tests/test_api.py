from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestAPI:

    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert "allowed_file_types" in data

    @patch("app.s3_service.s3_service.check_connection")
    def test_health_check_success(self, mock_check):
        """Test health check when S3 is healthy"""
        mock_check.return_value = True

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["s3_connection"] == "ok"

    @patch("app.s3_service.s3_service.check_connection")
    def test_health_check_failure(self, mock_check):
        """Test health check when S3 is unhealthy"""
        mock_check.return_value = False

        response = client.get("/health")
        assert response.status_code == 503

    @patch("app.s3_service.s3_service.generate_upload_url")
    def test_upload_url_success(self, mock_generate):
        """Test successful upload URL generation"""
        mock_generate.return_value = {
            "presigned_url": "https://s3.amazonaws.com/test-url",
            "file_key": "uploads/test.pdf",
            "expires_in": 600,
        }

        response = client.post(
            "/upload-url",
            json={"filename": "test.pdf", "content_type": "application/pdf"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "presigned_url" in data
        assert "file_key" in data
        assert "expires_in" in data

    @patch("app.s3_service.s3_service.generate_upload_url")
    def test_upload_url_invalid_file_type(self, mock_generate):
        """Test upload URL generation with invalid file type"""
        mock_generate.side_effect = ValueError("File type .exe not allowed")

        response = client.post("/upload-url", json={"filename": "malware.exe"})

        assert response.status_code == 400

    @patch("app.s3_service.s3_service.generate_download_url")
    def test_download_url_success(self, mock_generate):
        """Test successful download URL generation"""
        mock_generate.return_value = {
            "presigned_url": "https://s3.amazonaws.com/download-url",
            "file_key": "uploads/test.pdf",
            "expires_in": 600,
        }

        response = client.post("/download-url", json={"file_key": "uploads/test.pdf"})

        assert response.status_code == 200
        data = response.json()
        assert "presigned_url" in data

    @patch("app.s3_service.s3_service.generate_download_url")
    def test_download_url_file_not_found(self, mock_generate):
        """Test download URL generation for non-existent file"""
        mock_generate.side_effect = FileNotFoundError("File not found in S3")

        response = client.post(
            "/download-url", json={"file_key": "uploads/nonexistent.pdf"}
        )

        assert response.status_code == 404

    @patch("app.s3_service.s3_service.list_files")
    def test_list_files(self, mock_list):
        """Test file listing"""
        mock_list.return_value = {
            "files": [
                {
                    "key": "uploads/test.pdf",
                    "size": 1024,
                    "last_modified": "2024-01-01T12:00:00",
                    "etag": "abc123",
                }
            ],
            "count": 1,
        }

        response = client.get("/files")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["files"]) == 1

    @patch("app.s3_service.s3_service.delete_file")
    def test_delete_file_success(self, mock_delete):
        """Test successful file deletion"""
        mock_delete.return_value = True

        response = client.delete("/files/uploads/test.pdf")
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

    @patch("app.s3_service.s3_service.delete_file")
    def test_delete_file_failure(self, mock_delete):
        """Test file deletion failure"""
        mock_delete.side_effect = Exception("S3 error")

        response = client.delete("/files/uploads/test.pdf")
        assert response.status_code == 500
