"""
Helper module for writing, reading, and auditing execution load metadata for serving tables.
"""

from datetime import datetime

def log_load_metadata(conn, metadata: dict) -> None:
    """
    Inserts a row of operational pipeline execution log metrics into serving.load_metadata.
    
    Expected keys in metadata:
    - pipeline_execution_id
    - source_pipeline_execution_id
    - table_name
    - dataset_name
    - load_type ('UPSERT' or 'REPLACE')
    - status ('SUCCESS' or 'FAILED')
    - records_loaded
    - records_failed
    - rows_inserted
    - rows_updated
    - load_duration_ms
    - error_message (None or str)
    - start_time (datetime)
    - end_time (datetime)
    - generation_timestamp (datetime)
    """
    query = """
        INSERT INTO serving.load_metadata (
            pipeline_execution_id,
            source_pipeline_execution_id,
            table_name,
            dataset_name,
            load_type,
            status,
            records_loaded,
            records_failed,
            rows_inserted,
            rows_updated,
            load_duration_ms,
            error_message,
            start_time,
            end_time,
            generation_timestamp,
            rows_per_second,
            bytes_processed,
            database_write_rate,
            connection_wait_time_ms,
            transaction_duration_ms,
            retry_count,
            refresh_lag_minutes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    
    params = (
        metadata["pipeline_execution_id"],
        metadata.get("source_pipeline_execution_id"),
        metadata["table_name"],
        metadata["dataset_name"],
        metadata["load_type"],
        metadata["status"],
        metadata["records_loaded"],
        metadata["records_failed"],
        metadata.get("rows_inserted", 0),
        metadata.get("rows_updated", 0),
        metadata["load_duration_ms"],
        metadata.get("error_message"),
        metadata["start_time"],
        metadata["end_time"],
        metadata["generation_timestamp"],
        metadata.get("rows_per_second", 0.0),
        metadata.get("bytes_processed", 0),
        metadata.get("database_write_rate", 0.0),
        metadata.get("connection_wait_time_ms", 0.0),
        metadata.get("transaction_duration_ms", 0.0),
        metadata.get("retry_count", 0),
        metadata.get("refresh_lag_minutes", 0.0)
    )
    
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        # We do NOT commit here, as this function is executed within the scope of the caller's transaction
