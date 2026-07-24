"""
Client module for interacting with the RemoteOK API.
Responsible for:
- Fetching job listings and metadata
- Retry logic and timeout handling
- Custom exception handling
- Schema validation via schemas.remoteok
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from typing import Dict, Any

from ingestion.config import (
    REMOTEOK_API_URL,
    REQUEST_TIMEOUT,
    PIPELINE_VERSION,
    API_MAX_RETRIES,
    API_BACKOFF_FACTOR,
    API_STATUS_FORCELIST,
)
from ingestion.exceptions import (
    RemoteOKAPIError,
    RemoteOKTimeoutError,
    RemoteOKInvalidJSONError,
    ValidationError,
)
from ingestion.schemas.remoteok import validate_remoteok_response
from ingestion.logger import logger

def repair_mojibake(val: Any) -> Any:
    if isinstance(val, str):
        try:
            return val.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return val
    elif isinstance(val, dict):
        return {k: repair_mojibake(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [repair_mojibake(x) for x in val]
    return val

def fetch_jobs() -> Dict[str, Any]:
    """
    Orchestrates fetching, parsing, and validating RemoteOK job listings.
    
    Returns:
        Dict[str, Any]: A dictionary containing 'metadata' and 'jobs'.
        
    Raises:
        RemoteOKTimeoutError: If the request to the RemoteOK API times out.
        RemoteOKAPIError: If the RemoteOK API returns an error or is unreachable.
        RemoteOKInvalidJSONError: If the response is not valid JSON.
        ValidationError: If the response schema is invalid.
    """
    user_agent = f"CareerPulse/{PIPELINE_VERSION}"
    headers = {"User-Agent": user_agent}
    
    session = requests.Session()
    retry_strategy = Retry(
        total=API_MAX_RETRIES,
        backoff_factor=API_BACKOFF_FACTOR,
        status_forcelist=API_STATUS_FORCELIST,
        raise_on_status=False
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
    session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
    
    logger.info(f"Fetching RemoteOK jobs from {REMOTEOK_API_URL}")
    
    try:
        response = session.get(
            REMOTEOK_API_URL,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout occurred while connecting to RemoteOK API: {e}")
        raise RemoteOKTimeoutError(f"RemoteOK API request timed out: {e}") from e
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error response received from RemoteOK API: {e}")
        raise RemoteOKAPIError(f"RemoteOK API HTTP error: {e}") from e
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error occurred while connecting to RemoteOK API: {e}")
        raise RemoteOKAPIError(f"RemoteOK API connection failed: {e}") from e
        
    try:
        response.encoding = "utf-8"
        data = response.json()
        data = repair_mojibake(data)
    except ValueError as e:
        logger.error(f"Failed to decode JSON from RemoteOK response: {e}")
        raise RemoteOKInvalidJSONError(f"RemoteOK response is not valid JSON: {e}") from e
        
    try:
        validate_remoteok_response(data)
    except ValidationError as e:
        logger.error(f"RemoteOK response validation failed: {e}")
        raise
        
    # Metadata is the first element, jobs are the rest of the elements
    return {
        "metadata": data[0],
        "jobs": data[1:]
    }
