"""
Client examples for using the S3 Presigned URL API
"""
import requests
import json
from pathlib import Path

# API base URL
API_BASE_URL = "http://localhost:8000"

def upload_file_example():
    """Example of uploading a file using presigned URL"""
    
    # Step 1: Get presigned URL for upload
    filename = "example.pdf"
    upload_request = {
        "filename": filename,
        "content_type": "application/pdf"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/upload-url",
        json=upload_request
    )
    
    if response.status_code != 200:
        print(f"Failed to get upload URL: {response.text}")
        return
    
    upload_data = response.json()
    presigned_url = upload_data["presigned_url"]
    file_key = upload_data["file_key"]
    
    print(f"Got presigned URL for upload: {file_key}")
    
    # Step 2: Upload file directly to S3 using presigned URL
    # In a real scenario, you would read the actual file
    file_content = b"This is a sample PDF content"
    
    upload_response = requests.put(
        presigned_url,
        data=file_content,
        headers={"Content-Type": "application/pdf"}
    )
    
    if upload_response.status_code == 200:
        print(f"File uploaded successfully! File key: {file_key}")
        return file_key
    else:
        print(f"Upload failed: {upload_response.status_code} - {upload_response.text}")
        return None

def download_file_example(file_key: str):
    """Example of downloading a file using presigned URL"""
    
    # Step 1: Get presigned URL for download
    download_request = {
        "file_key": file_key
    }
    
    response = requests.post(
        f"{API_BASE_URL}/download-url",
        json=download_request
    )
    
    if response.status_code != 200:
        print(f"Failed to get download URL: {response.text}")
        return
    
    download_data = response.json()
    presigned_url = download_data["presigned_url"]
    
    print(f"Got presigned URL for download: {file_key}")
    
    # Step 2: Download file directly from S3 using presigned URL
    download_response = requests.get(presigned_url)
    
    if download_response.status_code == 200:
        print(f"File downloaded successfully! Size: {len(download_response.content)} bytes")
        
        # Save file locally
        local_filename = f"downloaded_{Path(file_key).name}"
        with open(local_filename, "wb") as f:
            f.write(download_response.content)
        print(f"File saved as: {local_filename}")
    else:
        print(f"Download failed: {download_response.status_code}")

def list_files_example():
    """Example of listing files"""
    response = requests.get(f"{API_BASE_URL}/files")
    
    if response.status_code == 200:
        files_data = response.json()
        print(f"Found {files_data['count']} files:")
        for file_info in files_data['files']:
            print(f"  - {file_info['key']} ({file_info['size']} bytes)")
    else:
        print(f"Failed to list files: {response.text}")

def health_check_example():
    """Example of health check"""
    response = requests.get(f"{API_BASE_URL}/health")
    
    if response.status_code == 200:
        health_data = response.json()
        print(f"API Status: {health_data['status']}")
        print(f"S3 Connection: {health_data['s3_connection']}")
    else:
        print(f"Health check failed: {response.text}")

if __name__ == "__main__":
    print("=== S3 Presigned URL API Client Examples ===\n")
    
    # Health check
    print("1. Health Check:")
    health_check_example()
    print()
    
    # Upload file
    print("2. Upload File:")
    file_key = upload_file_example()
    print()
    
    # List files
    print("3. List Files:")
    list_files_example()
    print()
    
    # Download file (if upload was successful)
    if file_key:
        print("4. Download File:")
        download_file_example(file_key)
        print()
    
    print("=== Examples completed ===")