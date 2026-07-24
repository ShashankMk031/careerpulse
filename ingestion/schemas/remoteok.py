"""
Schema validation for the RemoteOK API responses.
Responsible for verifying that the structure and types of the received payload conform
to expectations before any processing or uploading.
"""

from typing import Any
from ingestion.exceptions import ValidationError, RemoteOKEmptyResponseError

def validate_remoteok_response(data: Any) -> None:
    """
    Validates that the raw response from RemoteOK API matches the expected schema.
    
    Expected schema:
    - Top level is a non-empty list.
    - First element is a dictionary representing API metadata (must contain 'last_updated').
    - Subsequent elements (if any) are dictionaries representing job records (must contain at least 'id', 'position', 'company').
    
    Raises:
        ValidationError: If the data does not conform to the expected schema.
    """
    if not isinstance(data, list):
        raise ValidationError(
            f"Invalid RemoteOK API response structure: expected a list, but got {type(data).__name__}."
        )
        
    if not data:
        raise RemoteOKEmptyResponseError("Invalid RemoteOK API response: response list is empty.")
        
    # Validate Metadata (first item in the list)
    metadata = data[0]
    if not isinstance(metadata, dict):
        raise ValidationError(
            f"Invalid RemoteOK API response: first element (metadata) must be a dict, got {type(metadata).__name__}."
        )
        
    if "last_updated" not in metadata:
        raise ValidationError(
            "Invalid RemoteOK API response: metadata is missing the required 'last_updated' field."
        )
        
    # Validate Job Records (remaining items in the list)
    for idx, job in enumerate(data[1:], start=1):
        if not isinstance(job, dict):
            raise ValidationError(
                f"Invalid RemoteOK job record at index {idx}: expected a dict, got {type(job).__name__}."
            )
            
        required_fields = ["id", "position", "company"]
        missing_fields = [field for field in required_fields if field not in job]
        if missing_fields:
            raise ValidationError(
                f"Invalid RemoteOK job record at index {idx} (ID: {job.get('id', 'unknown')}): "
                f"missing required fields: {', '.join(missing_fields)}."
            )
