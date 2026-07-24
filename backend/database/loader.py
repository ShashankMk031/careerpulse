"""
Core dataset loading pipeline functions for CareerPulse Serving layer.
Performs S3 Parquet downloads, validation, type transformations, and transactional psycopg bulk upserts.
"""

import os
import tempfile
from datetime import datetime
import json
import boto3
import pyarrow.parquet as pq
import psycopg2.extras

# Mapping from logical dataset names to target database tables in the serving schema
DATASET_TABLE_MAP = {
    "company": "serving.company_analytics",
    "skills": "serving.skills_analytics",
    "geography": "serving.geography_analytics",
    "salary": "serving.salary_analytics",
    "technology": "serving.technology_analytics",
    "summary": "serving.hiring_summary"
}

def read_gold_dataset(s3_client, bucket: str, dataset_name: str) -> tuple[list[dict], datetime, str]:
    """
    Downloads and reads Gold Parquet files and reads their execution metadata from S3.
    
    Returns:
        tuple: (records: list[dict], generation_timestamp: datetime, pipeline_execution_id: str)
    """
    print(f"Retrieving S3 Gold dataset objects for: {dataset_name}...")
    
    # 1. Fetch latest metadata file to get pipeline_execution_id and generation_timestamp
    paginator = s3_client.get_paginator("list_objects_v2")
    metadata_prefix = f"metadata/gold/{dataset_name}/"
    meta_objects = []
    
    for page in paginator.paginate(Bucket=bucket, Prefix=metadata_prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".json"):
                meta_objects.append(obj)
                
    generation_timestamp = datetime.now()
    pipeline_execution_id = "UNKNOWN_EXEC"
    
    if meta_objects:
        # Sort by Key name to get the latest partition file chronologically
        latest_meta_key = sorted(meta_objects, key=lambda x: x["Key"])[-1]["Key"]
        try:
            print(f"Reading latest Gold metadata manifest: {latest_meta_key}")
            response = s3_client.get_object(Bucket=bucket, Key=latest_meta_key)
            meta_content = json.loads(response["Body"].read().decode("utf-8"))
            pipeline_execution_id = meta_content.get("pipeline_execution_id", "UNKNOWN_EXEC")
            gen_ts_str = meta_content.get("generation_timestamp")
            if gen_ts_str:
                # Parse ISO timestamp format
                generation_timestamp = datetime.fromisoformat(gen_ts_str.replace("Z", "+00:00"))
        except Exception as e:
            print(f"Warning: Failed to parse Gold metadata from S3: {e}")
            
    # 2. Download and read Parquet files
    parquet_prefix = f"gold/{dataset_name}/"
    parquet_objects = []
    for page in paginator.paginate(Bucket=bucket, Prefix=parquet_prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                parquet_objects.append(obj)
                
    records = []
    if not parquet_objects:
        print(f"Warning: No Parquet files found under S3 prefix: {parquet_prefix}")
        return records, generation_timestamp, pipeline_execution_id, 0
        
    total_bytes = sum(obj.get("Size", 0) for obj in parquet_objects)
    
    for obj in parquet_objects:
        s3_key = obj["Key"]
        print(f"Downloading Parquet object: {s3_key}")
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            s3_client.download_file(bucket, s3_key, tmp_path)
            table = pq.read_table(tmp_path)
            records.extend(table.to_pylist())
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    print(f"Successfully loaded {len(records)} records from S3 Parquet objects ({total_bytes} bytes).")
    return records, generation_timestamp, pipeline_execution_id, total_bytes

def validate_dataset(records: list[dict], dataset_name: str) -> tuple[list[dict], list[dict]]:
    """
    Validates the structure and constraints of records for the target dataset.
    
    Returns:
        tuple: (valid_records: list[dict], invalid_records: list[dict])
    """
    valid = []
    invalid = []
    
    for idx, rec in enumerate(records):
        is_valid = True
        error_reasons = []
        
        # 1. Primary key checks
        if dataset_name == "company" and not rec.get("company"):
            is_valid = False
            error_reasons.append("Missing required primary key: company")
        elif dataset_name == "skills" and not rec.get("tag"):
            is_valid = False
            error_reasons.append("Missing required primary key: tag")
        elif dataset_name == "geography" and (not rec.get("country") or not rec.get("region")):
            is_valid = False
            error_reasons.append("Missing required primary composite key: country or region")
        elif dataset_name == "salary" and not rec.get("salary_tier"):
            is_valid = False
            error_reasons.append("Missing required primary key: salary_tier")
        elif dataset_name == "technology" and not rec.get("tech_tag"):
            is_valid = False
            error_reasons.append("Missing required primary key: tech_tag")
            
        # 2. Check Constraint validations (Pre-validation before database write to identify failures)
        if dataset_name == "company":
            total_jobs = rec.get("total_jobs", 0)
            if total_jobs is None or total_jobs < 0:
                is_valid = False
                error_reasons.append(f"Constraint violation: total_jobs = {total_jobs}")
        elif dataset_name == "skills":
            demand = rec.get("job_demand_count", 0)
            if demand is None or demand < 0:
                is_valid = False
                error_reasons.append(f"Constraint violation: job_demand_count = {demand}")
        elif dataset_name == "summary":
            pct = rec.get("remote_percentage", 0.0)
            if pct is None or not (0.0 <= pct <= 100.0):
                is_valid = False
                error_reasons.append(f"Constraint violation: remote_percentage = {pct}")
                
        if is_valid:
            valid.append(rec)
        else:
            rec_copy = rec.copy()
            rec_copy["__error__"] = "; ".join(error_reasons)
            invalid.append(rec_copy)
            
    if invalid:
        print(f"Validation summary for '{dataset_name}': {len(valid)} valid, {len(invalid)} invalid.")
    return valid, invalid

def transform_dataset_if_needed(records: list[dict], dataset_name: str) -> list[dict]:
    """
    Applies any final type conversions or text standardizations necessary for PostgreSQL insertion.
    """
    transformed = []
    for rec in records:
        cleaned = rec.copy()
        
        # Clean company name
        if dataset_name == "company" and isinstance(cleaned.get("company"), str):
            cleaned["company"] = cleaned["company"].strip()
            
        # Standardize tag keys
        if dataset_name == "skills" and isinstance(cleaned.get("tag"), str):
            cleaned["tag"] = cleaned["tag"].strip().lower()
            
        transformed.append(cleaned)
        
    return transformed

def upsert_dataset(conn, records: list[dict], dataset_name: str) -> tuple[int, int]:
    """
    Performs psycopg bulk UPSERT or REPLACE logic inside a single transaction.
    
    Returns:
        tuple: (inserted_count: int, updated_count: int)
    """
    if not records:
        return 0, 0
        
    table = DATASET_TABLE_MAP[dataset_name]
    
    with conn.cursor() as cursor:
        if dataset_name == "summary":
            # Hiring Summary is a platform-wide snapshot: clear atomically and reload
            print(f"Executing atomic REPLACE refresh strategy on table: {table}...")
            cursor.execute(f"TRUNCATE TABLE {table};")
            
            # Formulate INSERT statement
            fields = [
                "total_jobs", "total_companies", "total_locations", "remote_jobs",
                "remote_percentage", "average_salary", "median_salary", "highest_salary",
                "highest_paying_company", "top_company", "top_skill", "top_country",
                "jobs_with_salary", "jobs_without_salary", "generation_timestamp"
            ]
            
            query = f"INSERT INTO {table} ({', '.join(fields)}) VALUES %s RETURNING 1;"
            template = "(" + ", ".join([f"%({f})s" for f in fields]) + ")"
            
            psycopg2.extras.execute_values(cursor, query, records, template=template)
            inserted_count = len(records)
            updated_count = 0
            
        else:
            # All other tables use UPSERT (INSERT ... ON CONFLICT DO UPDATE)
            print(f"Executing bulk UPSERT refresh strategy on table: {table}...")
            
            if dataset_name == "company":
                fields = [
                    "company", "total_jobs", "unique_locations", "avg_salary_min",
                    "avg_salary_max", "original_jobs_count", "highest_paying_role",
                    "latest_posting", "jobs_with_salary"
                ]
                conflict_target = "(company)"
                update_set = ", ".join([f"{f} = EXCLUDED.{f}" for f in fields if f != "company"])
                
            elif dataset_name == "skills":
                fields = ["tag", "job_demand_count", "avg_salary_min", "avg_salary_max", "salary_premium", "remote_jobs_count"]
                conflict_target = "(tag)"
                update_set = ", ".join([f"{f} = EXCLUDED.{f}" for f in fields if f != "tag"])
                
            elif dataset_name == "geography":
                fields = ["country", "region", "jobs_count", "avg_salary_min", "avg_salary_max", "company_count", "remote_count", "onsite_count", "hybrid_count"]
                conflict_target = "(country, region)"
                update_set = ", ".join([f"{f} = EXCLUDED.{f}" for f in fields if f not in ("country", "region")])
                
            elif dataset_name == "salary":
                fields = ["salary_tier", "jobs_count", "avg_salary_min", "avg_salary_max"]
                conflict_target = "(salary_tier)"
                update_set = ", ".join([f"{f} = EXCLUDED.{f}" for f in fields if f != "salary_tier"])
                
            elif dataset_name == "technology":
                fields = ["tech_tag", "job_demand_count", "avg_salary_min", "avg_salary_max", "top_company"]
                conflict_target = "(tech_tag)"
                update_set = ", ".join([f"{f} = EXCLUDED.{f}" for f in fields if f != "tech_tag"])
                
            query = f"""
                INSERT INTO {table} ({', '.join(fields)}) 
                VALUES %s 
                ON CONFLICT {conflict_target} 
                DO UPDATE SET {update_set}, updated_at = CURRENT_TIMESTAMP
                RETURNING (xmax = 0);
            """
            
            template = "(" + ", ".join([f"%({f})s" for f in fields]) + ")"
            
            # Execute values and fetch returns
            results = psycopg2.extras.execute_values(cursor, query, records, template=template, fetch=True)
            
            # xmax = 0 means row was inserted, xmax != 0 means row was updated (ON CONFLICT DO UPDATE)
            inserted_count = sum(1 for row in results if row[0] is True)
            updated_count = sum(1 for row in results if row[0] is False)
            
        print(f"Database response: {inserted_count} rows inserted, {updated_count} rows updated.")
        return inserted_count, updated_count
