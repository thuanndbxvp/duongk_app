"""
R2/S3 Storage Service — Tier 1 P0.
Handles file uploads to Cloudflare R2 or S3-compatible storage.
"""
from __future__ import annotations
import os
import uuid
from typing import Optional, BinaryIO
from botocore.exceptions import ClientError
import boto3


class StorageService:
    """Unified storage service for R2/S3 uploads."""
    
    def __init__(self):
        self.endpoint = os.getenv("R2_ENDPOINT") or os.getenv("S3_ENDPOINT")
        self.access_key = os.getenv("R2_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("R2_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.bucket = os.getenv("R2_BUCKET_UPLOADS") or os.getenv("S3_BUCKET_UPLOADS")
        self.region = os.getenv("R2_REGION", "auto")
        self.public_cdn = os.getenv("R2_PUBLIC_CDN") or os.getenv("S3_PUBLIC_CDN")
        
        if not all([self.endpoint, self.access_key, self.secret_key, self.bucket]):
            raise ValueError("Missing R2/S3 configuration. Check environment variables.")
        
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        )
    
    def upload_file(
        self,
        file_obj: BinaryIO,
        key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload a file to R2/S3.
        
        Args:
            file_obj: File-like object to upload
            key: Object key (path) in bucket
            content_type: MIME type
            metadata: Optional metadata dict
            
        Returns:
            Public URL of uploaded file
        """
        extra_args = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = metadata
        
        try:
            self.client.upload_fileobj(
                file_obj,
                self.bucket,
                key,
                ExtraArgs=extra_args,
            )
        except ClientError as e:
            raise UploadError(f"Upload failed: {e}")
        
        return self._get_public_url(key)
    
    def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload raw bytes to R2/S3.
        
        Args:
            data: Raw bytes to upload
            key: Object key (path) in bucket
            content_type: MIME type
            
        Returns:
            Public URL of uploaded file
        """
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        except ClientError as e:
            raise UploadError(f"Upload failed: {e}")
        
        return self._get_public_url(key)
    
    def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        method: str = "GET",
    ) -> str:
        """
        Generate a presigned URL for temporary access.
        
        Args:
            key: Object key (path) in bucket
            expires_in: URL expiration time in seconds
            method: HTTP method ('GET' or 'PUT')
            
        Returns:
            Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                f"get_object" if method == "GET" else "put_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            raise UploadError(f"Presigned URL generation failed: {e}")
    
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from R2/S3.
        
        Args:
            key: Object key (path) in bucket
            
        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            raise UploadError(f"Delete failed: {e}")
    
    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            key: Object key (path) in bucket
            
        Returns:
            True if file exists
        """
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
    
    def _get_public_url(self, key: str) -> str:
        """Generate public URL for a file."""
        if self.public_cdn:
            return f"{self.public_cdn.rstrip('/')}/{key}"
        return f"{self.endpoint.rstrip('/')}/{self.bucket}/{key}"


class UploadError(Exception):
    """Raised when upload fails."""
    pass


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create singleton storage service instance."""
    global _storage_service
    if _storage_service is None:
        try:
            _storage_service = StorageService()
        except ValueError as e:
            raise UploadError(f"Storage service not configured: {e}")
    return _storage_service
