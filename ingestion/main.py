"""
Main orchestrator for the CareerPulse ingestion pipeline.
Responsible for executing the complete flow from fetching data from RemoteOK API
to uploading the raw jobs and metadata companion files to Amazon S3.
"""

import sys
import json
import time
import hashlib
from dataclasses import dataclass, asdict
from typing import Optional

from ingestion.config import (
    SOURCE_NAME,
    PIPELINE_VERSION,
    SCHEMA_VERSION,
)
from ingestion.exceptions import (
    CareerPulseError,
    PipelineStatus,
    RemoteOKAPIError,
    RemoteOKTimeoutError,
    RemoteOKEmptyResponseError,
    RemoteOKInvalidJSONError,
    ValidationError,
    S3BucketNotFoundError,
    S3CredentialsError,
    S3UploadFailedError,
)
from ingestion.logger import logger, PipelineLoggerAdapter
from ingestion.remoteok import fetch_jobs
from ingestion.uploader import upload_json_to_s3, upload_jsonl_to_s3
from ingestion.utils import get_utc_timestamp, generate_pipeline_id, generate_s3_key

@dataclass
class PipelineResult:
    """Dataclass holding results and metrics of a pipeline execution run."""
    pipeline_id: str
    start_time: str
    end_time: str
    duration_ms: float
    api_response_time_ms: float
    payload_size_bytes: int
    jobs_upload_duration_ms: float
    metadata_upload_duration_ms: float
    records_processed: int
    records_uploaded: int
    status: PipelineStatus
    s3_jobs_key: str
    s3_metadata_key: str
    sha256: Optional[str] = None
    error_message: Optional[str] = None

def main() -> PipelineResult:
    """
    Orchestrates the ingestion pipeline execution.
    
    Flow:
    1. Pipeline Start & Generate Execution ID.
    2. Fetch RemoteOK Data and Measure API duration.
    3. Validate data and calculate jobs payload size & SHA-256 checksum.
    4. Generate metadata.
    5. Upload Jobs.
    6. Upload Metadata.
    7. Log Success & Pipeline Duration.
    8. Exit.
    
    Returns:
        PipelineResult: An object summarizing the pipeline run execution.
    """
    start_time = get_utc_timestamp()
    pipeline_id = generate_pipeline_id(start_time)
    
    # Initialize logger adapter to automatically prefix log messages with the Pipeline ID
    log = PipelineLoggerAdapter(logger, {"pipeline_id": pipeline_id})
    
    log.info("Pipeline Started")
    log.info(f"Execution ID: {pipeline_id}")
    
    # Metrics collection initialization
    pipeline_start_perf = time.perf_counter()
    api_duration_ms = 0.0
    payload_size = 0
    jobs_upload_duration_ms = 0.0
    metadata_upload_duration_ms = 0.0
    records_processed = 0
    records_uploaded = 0
    status = PipelineStatus.SUCCESS
    jobs_key = ""
    metadata_key = ""
    sha256_hash = None
    error_msg = None
    
    try:
        # Step 2: Fetch jobs from RemoteOK & Measure API duration
        log.info("API Request Started")
        api_start_perf = time.perf_counter()
        api_data = fetch_jobs()
        api_duration_ms = (time.perf_counter() - api_start_perf) * 1000.0
        
        log.info(f"API Duration: {api_duration_ms:.2f} ms")
        
        jobs = api_data["jobs"]
        api_metadata = api_data["metadata"]
        records_processed = len(jobs)
        log.info(f"Jobs Retrieved: {records_processed}")
        
        # Step 3: Generate S3 Keys
        jobs_key = generate_s3_key(SOURCE_NAME, start_time, "jobs")
        metadata_key = generate_s3_key(SOURCE_NAME, start_time, "metadata")
        
        # Calculate JSON serialization, payload size, and SHA-256 checksum metrics
        # For JSONL: exactly one record per line, UTF-8 encoded
        payload_str = "\n".join(json.dumps(job, ensure_ascii=False) for job in jobs)
        payload_bytes = payload_str.encode("utf-8")
        payload_size = len(payload_bytes)
        sha256_hash = hashlib.sha256(payload_bytes).hexdigest()
        
        log.info(f"Jobs SHA-256 Checksum generated: {sha256_hash}")
        
        # Step 4: Upload Jobs
        log.info("Uploading Jobs")
        jobs_upload_start_perf = time.perf_counter()
        upload_jsonl_to_s3(jobs, jobs_key)
        jobs_upload_duration_ms = (time.perf_counter() - jobs_upload_start_perf) * 1000.0
        records_uploaded = records_processed
        
        # Step 5: Construct and upload Ingestion Metadata
        api_last_updated = api_metadata.get("last_updated")
        
        # Measure pipeline duration up to metadata generation point
        current_pipeline_duration_ms = (time.perf_counter() - pipeline_start_perf) * 1000.0
        
        ingestion_metadata = {
            "pipeline_execution_id": pipeline_id,
            "pipeline_version": PIPELINE_VERSION,
            "schema_version": SCHEMA_VERSION,
            "source": SOURCE_NAME,
            "ingestion_timestamp": start_time.isoformat(),
            "api_last_updated": str(api_last_updated) if api_last_updated is not None else "",
            "record_count": records_uploaded,
            "api_record_count": records_processed,
            "jobs_file_size_bytes": payload_size,
            "sha256": sha256_hash,
            "pipeline_duration_ms": round(current_pipeline_duration_ms, 2),
            "status": status.value
        }
        
        log.info("Uploading Metadata")
        metadata_upload_start_perf = time.perf_counter()
        upload_json_to_s3(ingestion_metadata, metadata_key)
        metadata_upload_duration_ms = (time.perf_counter() - metadata_upload_start_perf) * 1000.0
        
        log.info("Upload successful")
        
    except RemoteOKTimeoutError as e:
        status = PipelineStatus.FAILED
        error_msg = f"RemoteOK API connection timed out: {e}"
        log.error(error_msg)
    except RemoteOKEmptyResponseError as e:
        status = PipelineStatus.FAILED
        error_msg = f"RemoteOK API returned empty response: {e}"
        log.error(error_msg)
    except RemoteOKInvalidJSONError as e:
        status = PipelineStatus.FAILED
        error_msg = f"RemoteOK API returned invalid JSON: {e}"
        log.error(error_msg)
    except RemoteOKAPIError as e:
        status = PipelineStatus.FAILED
        error_msg = f"RemoteOK API network or HTTP error: {e}"
        log.error(error_msg)
    except ValidationError as e:
        status = PipelineStatus.VALIDATION_FAILED
        error_msg = f"Payload schema validation failed: {e}"
        log.error(error_msg)
    except S3BucketNotFoundError as e:
        status = PipelineStatus.FAILED
        error_msg = f"S3 Bucket configuration error: {e}"
        log.error(error_msg)
    except S3CredentialsError as e:
        status = PipelineStatus.FAILED
        error_msg = f"AWS Credential resolution error: {e}"
        log.error(error_msg)
    except S3UploadFailedError as e:
        status = PipelineStatus.FAILED
        error_msg = f"S3 data upload failure: {e}"
        log.error(error_msg)
    except CareerPulseError as e:
        status = PipelineStatus.FAILED
        error_msg = f"CareerPulse pipeline error: {e}"
        log.error(error_msg)
    except Exception as e:
        status = PipelineStatus.UNKNOWN
        error_msg = f"Unexpected pipeline failure: {e}"
        log.error(error_msg, exc_info=True)
        
    # Calculate execution durations
    pipeline_end_perf = time.perf_counter()
    duration_ms = (pipeline_end_perf - pipeline_start_perf) * 1000.0
    end_time = get_utc_timestamp()
    
    # Structure pipeline result metrics
    result = PipelineResult(
        pipeline_id=pipeline_id,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        duration_ms=round(duration_ms, 2),
        api_response_time_ms=round(api_duration_ms, 2),
        payload_size_bytes=payload_size,
        jobs_upload_duration_ms=round(jobs_upload_duration_ms, 2),
        metadata_upload_duration_ms=round(metadata_upload_duration_ms, 2),
        records_processed=records_processed,
        records_uploaded=records_uploaded,
        status=status,
        s3_jobs_key=jobs_key,
        s3_metadata_key=metadata_key,
        sha256=sha256_hash,
        error_message=error_msg
    )
    
    log.info(f"Pipeline Duration: {duration_ms:.2f} ms")
    log.info("Pipeline Completed")
    logger.info(f"Pipeline Result Summary:\n{json.dumps(asdict(result), indent=2)}")
    
    return result

if __name__ == "__main__":
    pipeline_result = main()
    if pipeline_result.status != PipelineStatus.SUCCESS:
        sys.exit(1)
    sys.exit(0)