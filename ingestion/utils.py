"""
Utility helpers for the CareerPulse ingestion pipeline.
Responsible for:
- UTC timestamp generation
- Pipeline Execution ID generation
- Hive-style S3 partition path formatting
"""

import uuid
from datetime import datetime, timezone

def get_utc_timestamp() -> datetime:
    """
    Returns the current timestamp in UTC.
    
    Returns:
        datetime: The current UTC datetime object.
    """
    return datetime.now(timezone.utc)

def generate_pipeline_id(timestamp: datetime) -> str:
    """
    Generates a unique execution ID for a pipeline run.
    
    Format: YYYYMMDDTHHMMSSZ-hash (e.g., 20260629T172200Z-7f3c2d)
    
    Args:
        timestamp: The UTC timestamp of the pipeline execution start.
        
    Returns:
        str: A unique execution ID.
    """
    ts_str = timestamp.strftime("%Y%m%dT%H%M%SZ")
    random_suffix = uuid.uuid4().hex[:6]
    return f"{ts_str}-{random_suffix}"

def generate_s3_key(source: str, timestamp: datetime, content_type: str) -> str:
    """
    Generates a Hive-partitioned S3 key for a data object.
    
    Format:
        bronze/source={source}/year=YYYY/month=MM/day=DD/jobs_YYYYMMDDTHHMMSSZ[.metadata].json
        
    Args:
        source: The data source name (e.g., 'remoteok').
        timestamp: The UTC timestamp of the ingestion.
        content_type: The type of content ('jobs' or 'metadata').
        
    Returns:
        str: The fully-formed S3 key path.
    """
    year = timestamp.strftime("%Y")
    month = timestamp.strftime("%m")
    day = timestamp.strftime("%d")
    ts_str = timestamp.strftime("%Y%m%dT%H%M%SZ")
    
    if content_type == "metadata":
        return f"bronze/source={source}/year={year}/month={month}/day={day}/jobs_{ts_str}.metadata.json"
    else:
        return f"bronze/source={source}/year={year}/month={month}/day={day}/jobs_{ts_str}.jsonl"