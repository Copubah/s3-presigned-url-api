import os

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


settings = Settings()
