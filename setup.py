from setuptools import setup, find_packages

setup(
    name="s3-presigned-url-api",
    version="1.0.0",
    description="FastAPI application for S3 presigned URL generation",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "boto3==1.34.0",
        "python-dotenv==1.0.0",
        "pydantic==2.5.0",
        "python-multipart==0.0.6"
    ],
    python_requires=">=3.8",
)