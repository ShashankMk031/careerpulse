"""
Main orchestration application for loading Gold layer Parquet datasets from Amazon S3
into the Amazon RDS PostgreSQL serving database.
"""

import os
import sys
import time
from datetime import datetime, timezone
import boto3
from dotenv import load_dotenv

# Ensure backend package is discoverable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.connection import get_connection
from backend.database.loader import (
    read_gold_dataset,
    validate_dataset,
    transform_dataset_if_needed,
    upsert_dataset,
    DATASET_TABLE_MAP
)
from backend.database.metadata import log_load_metadata

# Load environment configuration
load_dotenv()

S3_BUCKET = os.getenv("S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

def run_serving_layer_loader() -> bool:
    """
    Orchestrates the S3-to-RDS loading pipeline for all 6 Gold datasets.
    
    Returns:
        bool: True if all datasets loaded successfully, False otherwise.
    """
    if not S3_BUCKET:
        print("Error: S3_BUCKET environment variable is not configured.")
        return False
        
    print(f"\nInitiating Serving Layer Load Pipeline from S3 Bucket: {S3_BUCKET}")
    print("Initializing AWS S3 Client...")
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    
    # Ordered list of Gold datasets to process
    datasets = ["company", "skills", "geography", "salary", "technology", "summary"]
    
    # Generate unique execution ID for this load pipeline run
    pipeline_execution_id = f"rds_load_{int(time.time())}"
    overall_success = True
    
    for name in datasets:
        print("\n" + "="*80)
        print(f"Processing Gold Dataset: {name}")
        print("="*80)
        
        start_time = datetime.now(timezone.utc)
        start_perf = time.perf_counter()
        
        records = []
        gen_timestamp = datetime.now(timezone.utc)
        source_exec_id = "UNKNOWN_EXEC"
        bytes_processed = 0
        
        # 1. Read Gold dataset from S3
        try:
            records, gen_timestamp, source_exec_id, bytes_processed = read_gold_dataset(s3_client, S3_BUCKET, name)
            if not records:
                print(f"No records found for dataset {name}, skipping load.")
                continue
        except Exception as e:
            print(f"Error reading S3 Parquet dataset '{name}': {e}")
            overall_success = False
            continue
            
        # 2. Validate data rules
        try:
            valid_records, invalid_records = validate_dataset(records, name)
            records_failed = len(invalid_records)
            records_loaded = len(valid_records)
        except Exception as e:
            print(f"Error validating dataset '{name}': {e}")
            overall_success = False
            continue
            
        # 3. Apply transformations
        try:
            transformed_records = transform_dataset_if_needed(valid_records, name)
        except Exception as e:
            print(f"Error transforming dataset '{name}': {e}")
            overall_success = False
            continue
            
        # 4. Transact database write with operational retries
        load_type = "REPLACE" if name == "summary" else "UPSERT"
        inserted_rows = 0
        updated_rows = 0
        status = "SUCCESS"
        error_msg = None
        
        retry_count = 0
        max_retries = 3
        connection_wait_time_ms = 0.0
        transaction_duration_ms = 0.0
        
        while retry_count <= max_retries:
            try:
                # Measure Connection Acquisition time
                start_acq = time.perf_counter()
                with get_connection() as conn:
                    acq_time_ms = (time.perf_counter() - start_acq) * 1000
                    connection_wait_time_ms += acq_time_ms
                    
                    # Measure SQL Transaction Duration
                    start_tx = time.perf_counter()
                    inserted_rows, updated_rows = upsert_dataset(conn, transformed_records, name)
                    tx_duration_ms = (time.perf_counter() - start_tx) * 1000
                    transaction_duration_ms += tx_duration_ms
                    
                    # Measure total process duration
                    end_perf = time.perf_counter()
                    duration_ms = int((end_perf - start_perf) * 1000)
                    end_time = datetime.now(timezone.utc)
                    
                    # Compute rate metrics
                    rows_per_second = records_loaded / (duration_ms / 1000.0) if duration_ms > 0 else 0.0
                    total_written = inserted_rows + updated_rows
                    database_write_rate = total_written / (tx_duration_ms / 1000.0) if tx_duration_ms > 0 else 0.0
                    
                    # Write success metadata
                    lag_minutes = (end_time - gen_timestamp).total_seconds() / 60.0
                    meta = {
                        "pipeline_execution_id": pipeline_execution_id,
                        "source_pipeline_execution_id": source_exec_id,
                        "table_name": DATASET_TABLE_MAP[name],
                        "dataset_name": name,
                        "load_type": load_type,
                        "status": status,
                        "records_loaded": records_loaded,
                        "records_failed": records_failed,
                        "rows_inserted": inserted_rows,
                        "rows_updated": updated_rows,
                        "load_duration_ms": duration_ms,
                        "error_message": error_msg,
                        "start_time": start_time,
                        "end_time": end_time,
                        "generation_timestamp": gen_timestamp,
                        "rows_per_second": rows_per_second,
                        "bytes_processed": bytes_processed,
                        "database_write_rate": database_write_rate,
                        "connection_wait_time_ms": connection_wait_time_ms,
                        "transaction_duration_ms": transaction_duration_ms,
                        "retry_count": retry_count,
                        "refresh_lag_minutes": lag_minutes
                    }
                    log_load_metadata(conn, meta)
                    print(f"Successfully loaded dataset {name} to RDS serving table.")
                    break  # Success - break retry loop
                    
            except Exception as e:
                print(f"Database write attempt {retry_count} failed for dataset '{name}': {e}")
                retry_count += 1
                if retry_count <= max_retries:
                    backoff_sec = 2 ** retry_count
                    print(f"Retrying in {backoff_sec} seconds...")
                    time.sleep(backoff_sec)
                else:
                    print(f"Max database load retries ({max_retries}) exceeded for dataset '{name}'. Logging failure.")
                    overall_success = False
                    status = "FAILED"
                    error_msg = str(e)
                    
                    # Write failure metadata record in a separate autonomous transaction
                    end_perf = time.perf_counter()
                    duration_ms = int((end_perf - start_perf) * 1000)
                    end_time = datetime.now(timezone.utc)
                    lag_minutes = (end_time - gen_timestamp).total_seconds() / 60.0
                    
                    try:
                        with get_connection() as failed_conn:
                            meta_fail = {
                                "pipeline_execution_id": pipeline_execution_id,
                                "source_pipeline_execution_id": source_exec_id,
                                "table_name": DATASET_TABLE_MAP[name],
                                "dataset_name": name,
                                "load_type": load_type,
                                "status": status,
                                "records_loaded": 0,
                                "records_failed": len(records),
                                "rows_inserted": 0,
                                "rows_updated": 0,
                                "load_duration_ms": duration_ms,
                                "error_message": error_msg,
                                "start_time": start_time,
                                "end_time": end_time,
                                "generation_timestamp": gen_timestamp,
                                "rows_per_second": 0.0,
                                "bytes_processed": bytes_processed,
                                "database_write_rate": 0.0,
                                "connection_wait_time_ms": connection_wait_time_ms,
                                "transaction_duration_ms": transaction_duration_ms,
                                "retry_count": retry_count,
                                "refresh_lag_minutes": lag_minutes
                            }
                            log_load_metadata(failed_conn, meta_fail)
                        print("Failed metadata log saved successfully.")
                    except Exception as meta_e:
                        print(f"Critical Error: Failed to log failure metadata to database: {meta_e}")
                
    return overall_success

def main():
    success = run_serving_layer_loader()
    if not success:
        print("\nPipeline execution encountered failures. See logs for details.")
        sys.exit(1)
    else:
        print("\nAll Gold datasets successfully synchronized to RDS Serving Layer!")

if __name__ == "__main__":
    main()
