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
    Generates an S3 key for Bronze data or metadata following the canonical layout:
    - Jobs:     bronze/source={source}-active/year=YYYY/month=MM/day=DD/jobs_YYYYMMDDTHHMMSSZ.jsonl
    - Metadata: bronze/metadata/{source}/year=YYYY/month=MM/day=DD/jobs_YYYYMMDDTHHMMSSZ.metadata.json
        
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
    
    base_source = source.removesuffix("-active")
    
    if content_type == "metadata":
        return f"bronze/metadata/{base_source}/year={year}/month={month}/day={day}/jobs_{ts_str}.metadata.json"
    
    # RemoteOK canonical crawler target in Bronze is source=remoteok-active
    source_partition = "remoteok-active" if base_source == "remoteok" else source
    return f"bronze/source={source_partition}/year={year}/month={month}/day={day}/jobs_{ts_str}.jsonl"