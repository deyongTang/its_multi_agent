from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
import io
import urllib3

# Suppress insecure request warnings if using HTTP or self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from config.settings import settings
    from infrastructure.logger import logger
except ModuleNotFoundError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.getcwd())
    from config.settings import settings
    from infrastructure.logger import logger

class MinioStorageClient:
    """
    MinIO Object Storage Client Wrapper
    """

    def __init__(self):
        try:
            self.client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
                cert_check=False if not settings.MINIO_SECURE else True
            )
            self.bucket_name = settings.MINIO_BUCKET
            logger.info(f"MinIO Client initialized. Endpoint: {settings.MINIO_ENDPOINT}, Bucket: {self.bucket_name}")
            self._ensure_bucket_exists()
        except Exception as e:
            logger.error(f"Failed to initialize MinIO Client: {e}")
            raise

    def _ensure_bucket_exists(self):
        """Ensure the target bucket exists."""
        try:
            found = self.client.bucket_exists(self.bucket_name)
            if not found:
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.debug(f"Bucket '{self.bucket_name}' already exists.")
        except S3Error as e:
            logger.error(f"Error checking/creating bucket: {e}")
            raise

    def upload_file(self, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """
        Upload bytes data to MinIO.
        
        Args:
            object_name: The path/name of the object in the bucket.
            data: The file content in bytes.
            content_type: MIME type of the file.

        Returns:
            str: The object name (path) if successful.
        """
        try:
            data_stream = io.BytesIO(data)
            data_length = len(data)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=data_stream,
                length=data_length,
                content_type=content_type
            )
            logger.info(f"Uploaded {object_name} to MinIO successfully.")
            return object_name
        except S3Error as e:
            logger.error(f"Failed to upload {object_name}: {e}")
            raise

    def download_file(self, object_name: str) -> bytes:
        """
        Download a file from MinIO as bytes.

        Args:
            object_name: The path/name of the object to download.

        Returns:
            bytes: The file content.
        """
        response = None
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            return response.read()
        except S3Error as e:
            logger.error(f"Failed to download {object_name}: {e}")
            raise
        finally:
            if response:
                response.close()
                
    def file_exists(self, object_name: str) -> bool:
        """Check if a file exists in the bucket."""
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            logger.error(f"Error checking file existence for {object_name}: {e}")
            return False

    def get_presigned_url(self, object_name: str, expires_hours: int = 1) -> str:
        """Generate a presigned URL for downloading the file."""
        try:
            from datetime import timedelta
            url = self.client.get_presigned_url(
                "GET",
                self.bucket_name,
                object_name,
                expires=timedelta(hours=expires_hours),
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL for {object_name}: {e}")
            return ""

if __name__ == "__main__":
    # Test block
    try:
        client = MinioStorageClient()
        test_filename = "test/hello.txt"
        test_content = b"Hello MinIO!"
        
        print(f"Uploading {test_filename}...")
        client.upload_file(test_filename, test_content, "text/plain")
        
        print(f"Checking existence...")
        if client.file_exists(test_filename):
            print("File exists!")
        
        print(f"Downloading {test_filename}...")
        downloaded = client.download_file(test_filename)
        print(f"Content: {downloaded.decode()}")
        
    except Exception as e:
        print(f"Test failed: {e}")
