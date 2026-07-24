"""
Custom exception hierarchy and status enumerations for the CareerPulse ingestion pipeline.
All custom exceptions inherit from the base class CareerPulseError.
"""

from enum import Enum

class PipelineStatus(str, Enum):
    """Enumeration of ingestion pipeline run statuses."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    UNKNOWN = "UNKNOWN"


class CareerPulseError(Exception):
    """Base exception for all CareerPulse errors."""
    pass


class RemoteOKError(CareerPulseError):
    """Base exception for all RemoteOK client errors."""
    pass


class RemoteOKAPIError(RemoteOKError):
    """Raised when the RemoteOK API returns a non-2xx status code."""
    pass


class RemoteOKTimeoutError(RemoteOKError):
    """Raised when the connection to RemoteOK API times out."""
    pass


class RemoteOKEmptyResponseError(RemoteOKError):
    """Raised when the RemoteOK API returns an empty response."""
    pass


class RemoteOKInvalidJSONError(RemoteOKError):
    """Raised when the response from RemoteOK cannot be decoded as JSON."""
    pass


class UploaderError(CareerPulseError):
    """Base exception for all uploader errors."""
    pass


class S3BucketNotFoundError(UploaderError):
    """Raised when the target S3 bucket does not exist."""
    pass


class S3CredentialsError(UploaderError):
    """Raised when S3 credentials are missing or invalid."""
    pass


class S3UploadFailedError(UploaderError):
    """Raised when an object fails to upload to S3."""
    pass


class ValidationError(CareerPulseError):
    """Raised when validating data against a schema fails."""
    pass
