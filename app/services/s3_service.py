import os
import uuid
from typing import BinaryIO, Optional, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """
    Service for handling file uploads to AWS S3.
    
    Uses environment variables for configuration:
    - AWS_ACCESS_KEY_ID: AWS access key
    - AWS_SECRET_ACCESS_KEY: AWS secret key
    - AWS_REGION: AWS region (default: us-east-1)
    - S3_BUCKET_NAME: S3 bucket name
    - S3_PRODUCT_IMAGES_FOLDER: Folder for product images (default: product-images)
    """
    
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.product_images_folder = os.getenv("S3_PRODUCT_IMAGES_FOLDER", "product-images")
        
        # Initialize S3 client
        self.s3_client: Optional[Any] = None
        if self.aws_access_key_id and self.aws_secret_access_key and self.bucket_name:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.aws_region
                )
                logger.info(f"S3 client initialized successfully for bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {str(e)}")
                self.s3_client = None
        else:
            logger.warning("S3 configuration incomplete. Image upload will not be available.")
    
    def is_configured(self) -> bool:
        """Check if S3 is properly configured."""
        return self.s3_client is not None
    
    def _validate_configuration(self):
        """Validate that S3 is configured, raise exception if not."""
        if not self.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="S3 service is not configured. Please contact administrator."
            )
    
    def _validate_image_file(self, file: UploadFile) -> int:
        """
        Validate uploaded file is an image and within size limits.
        
        Args:
            file: The uploaded file
            
        Returns:
            File size in bytes
            
        Raises:
            HTTPException 400: If file is invalid
        """
        # Check file exists
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Check content type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type '{file.content_type}'. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Check file size (10MB max)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning - CRITICAL for upload
        
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size / (1024*1024):.2f}MB) exceeds maximum allowed size of {max_size / (1024*1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        return file_size
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename to prevent collisions.
        
        Args:
            original_filename: The original filename
            
        Returns:
            Unique filename with timestamp and UUID
        """
        # Get file extension
        file_ext = os.path.splitext(original_filename)[1].lower()
        if not file_ext:
            file_ext = '.jpg'  # Default extension
        
        # Generate unique name: timestamp-uuid.ext
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        unique_filename = f"{timestamp}_{unique_id}{file_ext}"
        
        return unique_filename
    
    def upload_product_image(
        self,
        file: UploadFile,
        product_id: Optional[int] = None
    ) -> str:
        """
        Upload a product image to S3.
        
        Args:
            file: The image file to upload
            product_id: Optional product ID to organize images by product
            
        Returns:
            The public URL of the uploaded image
            
        Raises:
            HTTPException 503: If S3 is not configured
            HTTPException 400: If file is invalid
            HTTPException 500: If upload fails
        """
        self._validate_configuration()
        file_size = self._validate_image_file(file)
        
        # Type narrowing: s3_client is guaranteed to be not None after validation
        assert self.s3_client is not None
        
        try:
            # Generate unique filename
            filename = file.filename or "image.jpg"  # Default if filename is None
            unique_filename = self._generate_unique_filename(filename)
            
            # Construct S3 key (path in bucket)
            if product_id:
                s3_key = f"{self.product_images_folder}/product-{product_id}/{unique_filename}"
            else:
                s3_key = f"{self.product_images_folder}/{unique_filename}"
            
            # CRITICAL: Read file content into memory to avoid "closed file" errors
            # FastAPI's UploadFile can close the underlying file handle unexpectedly
            file.file.seek(0)
            file_content = file.file.read()
            
            # Prepare upload arguments
            extra_args = {
                'ContentType': file.content_type or 'image/jpeg',
            }
            
            # Try with ACL first, fallback without ACL if bucket doesn't allow it
            try:
                extra_args['ACL'] = 'public-read'
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_content,
                    **extra_args
                )
            except ClientError as acl_error:
                # If ACL fails, try without it (bucket might have public access via policy)
                if 'AccessControlListNotSupported' in str(acl_error):
                    logger.warning(f"ACL not supported for bucket {self.bucket_name}, uploading without ACL")
                    del extra_args['ACL']
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        Body=file_content,
                        **extra_args
                    )
                else:
                    raise  # Re-raise if it's a different ACL error
            
            # Construct public URL
            image_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            
            logger.info(f"Successfully uploaded image to S3: {s3_key} (size: {file_size / 1024:.2f}KB)")
            return image_url
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"S3 ClientError [{error_code}]: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image to S3 [{error_code}]: {error_message}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during image upload: {str(e)}"
            )
    
    def upload_multiple_product_images(
        self,
        files: list[UploadFile],
        product_id: Optional[int] = None,
        max_images: int = 10
    ) -> list[str]:
        """
        Upload multiple product images to S3.
        
        Args:
            files: List of image files to upload
            product_id: Optional product ID
            max_images: Maximum number of images allowed (default: 10)
            
        Returns:
            List of public URLs for uploaded images
            
        Raises:
            HTTPException 400: If too many files, no files, or ALL uploads fail
            HTTPException 503: If S3 not configured
            
        Note:
            If SOME uploads succeed and others fail, returns successful URLs
            and logs warnings about failures. If ALL fail, raises exception.
        """
        if len(files) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided for upload"
            )
        
        if len(files) > max_images:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {max_images} images allowed per upload"
            )
        
        uploaded_urls = []
        failed_uploads = []
        
        for idx, file in enumerate(files):
            try:
                url = self.upload_product_image(file, product_id)
                uploaded_urls.append(url)
                logger.info(f"Upload {idx + 1}/{len(files)}: SUCCESS - {file.filename}")
            except HTTPException as e:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": e.detail,
                    "status_code": e.status_code
                })
                logger.error(f"Upload {idx + 1}/{len(files)}: FAILED - {file.filename}: {e.detail}")
            except Exception as e:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": str(e),
                    "status_code": 500
                })
                logger.error(f"Upload {idx + 1}/{len(files)}: FAILED - {file.filename}: {str(e)}")
        
        # If ALL uploads failed, raise an exception with details
        if len(uploaded_urls) == 0:
            error_details = "; ".join([f"{f['filename']}: {f['error']}" for f in failed_uploads[:3]])
            if len(failed_uploads) > 3:
                error_details += f" (and {len(failed_uploads) - 3} more)"
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"All image uploads failed. Errors: {error_details}"
            )
        
        # If some uploads failed, log comprehensive warning
        if failed_uploads:
            logger.warning(
                f"Partial upload success: {len(uploaded_urls)}/{len(files)} succeeded, "
                f"{len(failed_uploads)} failed. Failed files: {[f['filename'] for f in failed_uploads]}"
            )
        else:
            logger.info(f"All {len(files)} images uploaded successfully")
        
        return uploaded_urls
    
    def delete_image(self, image_url: str) -> bool:
        """
        Delete an image from S3 given its URL.
        
        Args:
            image_url: The public URL of the image
            
        Returns:
            True if deletion was successful
            
        Raises:
            HTTPException 503: If S3 not configured
            HTTPException 500: If deletion fails
        """
        self._validate_configuration()
        
        # Type narrowing: s3_client is guaranteed to be not None after validation
        assert self.s3_client is not None
        
        try:
            # Extract S3 key from URL
            # URL format: https://bucket.s3.region.amazonaws.com/key
            s3_key = image_url.split(f"{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/")[1]
            
            # Delete from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"Successfully deleted image from S3: {s3_key}")
            return True
            
        except IndexError:
            logger.error(f"Invalid S3 URL format: {image_url}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image URL format"
            )
        except ClientError as e:
            logger.error(f"S3 deletion failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete image from S3: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during S3 deletion: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during image deletion: {str(e)}"
            )
    
    def delete_multiple_images(self, image_urls: list[str]) -> dict:
        """
        Delete multiple images from S3.
        
        Args:
            image_urls: List of image URLs to delete
            
        Returns:
            Dictionary with deletion results
        """
        results = {
            "deleted": [],
            "failed": []
        }
        
        for url in image_urls:
            try:
                self.delete_image(url)
                results["deleted"].append(url)
            except HTTPException as e:
                results["failed"].append({
                    "url": url,
                    "error": e.detail
                })
                logger.warning(f"Failed to delete {url}: {e.detail}")
        
        return results


# Singleton instance
s3_service = S3Service()


def get_s3_service() -> S3Service:
    """Dependency to get S3Service instance."""
    return s3_service
