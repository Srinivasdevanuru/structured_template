import os
import boto3
import tempfile
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
import streamlit as st

class ObjectStorage:
    """Object storage handler for video files using AWS S3 or compatible storage"""
    
    def __init__(self):
        self.s3_client = None
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'medibox-videos')
        self.setup_s3_client()
    
    def setup_s3_client(self):
        """Initialize S3 client with environment credentials"""
        try:
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            
            if aws_access_key and aws_secret_key:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=aws_region
                )
            else:
                # Try using default credentials (IAM roles, etc.)
                self.s3_client = boto3.client('s3')
                
        except (ClientError, NoCredentialsError) as e:
            st.warning("Object storage not configured. Files will be processed locally only.")
            self.s3_client = None
    
    def is_available(self) -> bool:
        """Check if object storage is available"""
        return self.s3_client is not None
    
    def upload_file(self, file_obj, filename: str) -> Optional[str]:
        """
        Upload file to object storage
        
        Args:
            file_obj: File object to upload
            filename: Name for the stored file
            
        Returns:
            S3 key if successful, None if failed
        """
        if not self.is_available():
            return None
            
        try:
            s3_key = f"videos/{filename}"
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, s3_key)
            return s3_key
        except ClientError as e:
            st.error(f"Failed to upload file to storage: {str(e)}")
            return None
    
    def download_file(self, s3_key: str) -> Optional[str]:
        """
        Download file from object storage to temporary location
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Local file path if successful, None if failed
        """
        if not self.is_available():
            return None
            
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            self.s3_client.download_fileobj(self.bucket_name, s3_key, temp_file)
            temp_file.close()
            return temp_file.name
        except ClientError as e:
            st.error(f"Failed to download file from storage: {str(e)}")
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from object storage
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if successful, False if failed
        """
        if not self.is_available():
            return False
            
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            st.error(f"Failed to delete file from storage: {str(e)}")
            return False
    
    def list_files(self, prefix: str = "videos/") -> list:
        """
        List files in object storage
        
        Args:
            prefix: S3 prefix to filter objects
            
        Returns:
            List of object keys
        """
        if not self.is_available():
            return []
            
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except ClientError as e:
            st.error(f"Failed to list files in storage: {str(e)}")
            return []
    
    def get_file_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for file access
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL if successful, None if failed
        """
        if not self.is_available():
            return None
            
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            st.error(f"Failed to generate file URL: {str(e)}")
            return None

# Global storage instance
storage = ObjectStorage()