"""
Uploader module for persisting raw payloads to Amazon S3.
Responsible for:
- Initializing the boto3 S3 client using the default credential chain.
- Uploading JSON payloads to the Bronze S3 bucket.
- Retry logic with exponential backoff for transient S3 failures.
- Raising custom exceptions for distinct failure modes.
"""

import json
import time
from typing import Dict, Any, Union
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ingestion.config import (
    S3_BUCKET,
    AWS_REGION,
    S3_MAX_RETRIES,
    S3_BACKOFF_FACTOR,
    S3_TRANSIENT_ERRORS,
)
from ingestion.exceptions import (
    S3BucketNotFoundError,
    S3CredentialsError,
    S3UploadFailedError,
    
)
from ingestion.logger import logger

def _upload_bytes_to_s3(payload_bytes: bytes, s3_key: str, content_type: str) -> str:
    """
    Private helper to upload raw bytes to S3 with retry logic and error handling.
    """
    # Initialize boto3 S3 client using default credential chain
    try:
        s3_client = boto3.client("s3", region_name=AWS_REGION)
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}")
        raise S3CredentialsError(f"Failed to initialize S3 client: {e}") from e

    attempt = 0
    while True:
        try:
            logger.info(
                f"Uploading payload to S3 (bucket: {S3_BUCKET}, key: {s3_key}). "
                f"Attempt {attempt + 1}/{S3_MAX_RETRIES + 1}"
            )
            
            # Perform S3 put object
            response = s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=payload_bytes,
                ContentType=content_type
            )
            
            # Validate status code in ResponseMetadata
            response_metadata = response.get("ResponseMetadata", {})
            status_code = response_metadata.get("HTTPStatusCode")
            
            if status_code != 200:
                raise S3UploadFailedError(
                    f"S3 upload returned a non-200 status code: {status_code}"
                )
                
            etag = response.get("ETag", "").strip('"')
            logger.info(f"Upload completed successfully. ETag: {etag}")
            return etag
            
        except NoCredentialsError as e:
            logger.error(f"AWS credentials not found: {e}")
            raise S3CredentialsError("AWS credentials not found.") from e
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            
            # Check for specific permanent errors
            if error_code == "NoSuchBucket":
                logger.error(f"The target S3 bucket '{S3_BUCKET}' does not exist: {e}")
                raise S3BucketNotFoundError(f"S3 Bucket '{S3_BUCKET}' not found.") from e
            elif error_code in ("InvalidAccessKeyId", "SignatureDoesNotMatch", "AuthFailure", "ExpiredToken"):
                logger.error(f"AWS credentials validation failed: {e}")
                raise S3CredentialsError(f"AWS credential validation failed: {error_code}") from e
                
            # If the error is transient and we have retries remaining, retry with backoff
            is_transient = error_code in S3_TRANSIENT_ERRORS or "timeout" in str(e).lower()
            if is_transient and attempt < S3_MAX_RETRIES:
                attempt += 1
                backoff_duration = S3_BACKOFF_FACTOR * (2 ** (attempt - 1))
                logger.warning(
                    f"Transient S3 upload error ({error_code}). "
                    f"Retrying in {backoff_duration:.2f}s... (Attempt {attempt}/{S3_MAX_RETRIES})"
                )
                time.sleep(backoff_duration)
                continue
                
            logger.error(f"AWS S3 ClientError occurred during upload: {e}")
            raise S3UploadFailedError(f"S3 upload failed with ClientError: {e}") from e
            
        except Exception as e:
            # For network-level timeouts or connection resets raised by urllib3/botocore
            if attempt < S3_MAX_RETRIES:
                attempt += 1
                backoff_duration = S3_BACKOFF_FACTOR * (2 ** (attempt - 1))
                logger.warning(
                    f"Unexpected S3 upload error ({type(e).__name__}: {e}). "
                    f"Retrying in {backoff_duration:.2f}s... (Attempt {attempt}/{S3_MAX_RETRIES})"
                )
                time.sleep(backoff_duration)
                continue
                
            logger.error(f"Unexpected error during S3 upload: {e}")
            raise S3UploadFailedError(f"Unexpected error during S3 upload: {e}") from e

def upload_json_to_s3(data: Union[Dict[str, Any], list], s3_key: str) -> str:
    """
    Serializes a Python dict or list to a JSON string and uploads it to Amazon S3.
    
    Includes retry logic with exponential backoff for transient failures.
    Verifies that the upload succeeded (HTTP status 200) and returns the ETag.
    
    Args:
        data: The dictionary or list to serialize and upload.
        s3_key: The target S3 key path.
        
    Returns:
        str: The ETag of the uploaded S3 object.
        
    Raises:
        S3BucketNotFoundError: If the target bucket does not exist.
        S3CredentialsError: If AWS credentials are missing or invalid.
        S3UploadFailedError: If the upload failed after max retries.
    """
    if not S3_BUCKET:
        raise S3UploadFailedError("S3_BUCKET environment variable is not configured.")
        
    # Serialize to JSON string with indent for clean Bronze readability
    payload_str = json.dumps(data, indent=2, ensure_ascii=False)
    payload_bytes = payload_str.encode("utf-8")
    
    return _upload_bytes_to_s3(payload_bytes, s3_key, "application/json; charset=utf-8")

def upload_jsonl_to_s3(records: list[Dict[str, Any]], s3_key: str) -> str:
    """
    Serializes a list of dictionaries to JSON Lines format (one record per line)
    and uploads the payload to Amazon S3.
    
    Includes retry logic with exponential backoff for transient failures.
    Verifies that the upload succeeded (HTTP status 200) and returns the ETag.
    
    Args:
        records: A list of dictionaries representing the records to upload.
        s3_key: The target S3 key path.
        
    Returns:
        str: The ETag of the uploaded S3 object.
        
    Raises:
        S3BucketNotFoundError: If the target bucket does not exist.
        S3CredentialsError: If AWS credentials are missing or invalid.
        S3UploadFailedError: If the upload failed after max retries.
    """
    if not S3_BUCKET:
        raise S3UploadFailedError("S3_BUCKET environment variable is not configured.")
        
    payload_str = "\n".join(json.dumps(rec, ensure_ascii=False) for rec in records)
    payload_bytes = payload_str.encode("utf-8")
    
    return _upload_bytes_to_s3(payload_bytes, s3_key, "application/x-ndjson; charset=utf-8")
