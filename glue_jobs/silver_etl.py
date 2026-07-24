"""
CareerPulse Silver Layer PySpark ETL Script.
Responsible for:
- Reading Bronze dataset from Glue Data Catalog.
- Extracting and flattening the nested 'array' structures.
- Validating schemas and schema type casting.
- Separating business validation rule failures into a quarantined S3 dataset partitioned by reason.
- Deduplicating job listings by ID, keeping the newest entry based on epoch time.
- Standardizing and cleaning text/tags/timestamps.
- Exporting valid data to Silver S3 path as partitioned Parquet files with Snappy compression.
- Generating operational metadata metrics.
"""

import os
import sys
import time
from datetime import datetime, timezone
import boto3
import json

from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, when, trim, lower, lit, desc, row_number, to_timestamp, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, LongType, IntegerType, BooleanType, TimestampType, ArrayType
from pyspark.sql.window import Window

# Define the explicit destination schema for the Silver Layer
SILVER_SCHEMA = StructType([
    StructField("id", LongType(), True),
    StructField("slug", StringType(), True),
    StructField("epoch", LongType(), True),
    StructField("date_posted", TimestampType(), True),
    StructField("company", StringType(), True),
    StructField("company_logo", StringType(), True),
    StructField("position", StringType(), True),
    StructField("tags", ArrayType(StringType()), True),
    StructField("description", StringType(), True),
    StructField("location", StringType(), True),
    StructField("country", StringType(), True),
    StructField("region", StringType(), True),
    StructField("remote_flag", BooleanType(), True),
    StructField("apply_url", StringType(), True),
    StructField("salary_min", IntegerType(), True),
    StructField("salary_max", IntegerType(), True),
    StructField("logo", StringType(), True),
    StructField("url", StringType(), True),
    StructField("original", BooleanType(), True),
    StructField("year", StringType(), True),
    StructField("month", StringType(), True),
    StructField("day", StringType(), True)
])

def validate_schema(df):
    """
    Validates that the source DataFrame contains the expected nested job records
    and maps columns to their appropriate types.
    """
    # If the exploded nested array isn't present, the schema is invalid
    if "array" not in df.columns:
        raise ValueError("Source DataFrame is missing the required nested 'array' column.")
    
    # Retrieve actual fields in the exploded 'job' struct to handle missing columns dynamically (schema drift)
    job_fields = []
    try:
        job_fields = df.schema["array"].dataType.elementType.fieldNames()
    except Exception as e:
        print(f"Warning: Could not extract job fields from catalog schema: {e}")
        
    def get_job_col(field_name, default_type):
        if field_name in job_fields:
            return col(f"job.{field_name}").cast(default_type)
        else:
            return lit(None).cast(default_type)

    # Explode the jobs array
    df_flat = df.select(explode("array").alias("job"), "year", "month", "day")
    
    # Project and cast fields to the explicit Silver schema types
    df_projected = df_flat.select(
        get_job_col("id", LongType()).alias("id"),
        get_job_col("slug", StringType()).alias("slug"),
        get_job_col("epoch", LongType()).alias("epoch"),
        (col("job.date") if "date" in job_fields else lit(None).cast(StringType())).alias("date_raw"),
        get_job_col("company", StringType()).alias("company"),
        get_job_col("company_logo", StringType()).alias("company_logo"),
        get_job_col("position", StringType()).alias("position"),
        get_job_col("tags", ArrayType(StringType())).alias("tags"),
        get_job_col("description", StringType()).alias("description"),
        get_job_col("location", StringType()).alias("location"),
        get_job_col("apply_url", StringType()).alias("apply_url"),
        (when(col("job.salary_min").cast(IntegerType()) > 0, col("job.salary_min").cast(IntegerType())).otherwise(lit(None)) if "salary_min" in job_fields else lit(None).cast(IntegerType())).alias("salary_min"),
        (when(col("job.salary_max").cast(IntegerType()) > 0, col("job.salary_max").cast(IntegerType())).otherwise(lit(None)) if "salary_max" in job_fields else lit(None).cast(IntegerType())).alias("salary_max"),
        get_job_col("logo", StringType()).alias("logo"),
        get_job_col("url", StringType()).alias("url"),
        get_job_col("original", BooleanType()).alias("original"),
        col("year").cast(StringType()).alias("yearProjected"),
        col("month").cast(StringType()).alias("monthProjected"),
        col("day").cast(StringType()).alias("dayProjected")
    )
    
    # Restore standard partition column names
    df_projected = df_projected.withColumnRenamed("yearProjected", "year") \
                               .withColumnRenamed("monthProjected", "month") \
                               .withColumnRenamed("dayProjected", "day")
                               
    return df_projected

def validate_business_rules(df):
    """
    Evaluates business data quality checks on the flattened job records.
    Adds a 'reason' column indicating the failure type for non-compliant records.
    """
    # Business Rules:
    # 1. Missing Required Fields: id, company, and position must not be null/empty
    # 2. Invalid Salary Bounds: If both min/max salary exist, max must be >= min
    df_validated = df.withColumn(
        "reason",
        when(
            col("id").isNull() | 
            col("company").isNull() | (trim(col("company")) == "") | 
            col("position").isNull() | (trim(col("position")) == ""),
            lit("missing_required_fields")
        ).when(
            col("salary_min").isNotNull() & col("salary_max").isNotNull() & (col("salary_max") < col("salary_min")),
            lit("invalid_salary")
        ).otherwise(lit(None))
    )
    return df_validated

def clean_dataframe(df):
    """
    Trims string fields and normalizes values for valid records.
    """
    # Trim leading/trailing whitespace from string columns
    for field in df.schema.fields:
        if isinstance(field.dataType, StringType) and field.name != "reason":
            df = df.withColumn(field.name, trim(col(field.name)))
            
    return df

def transform_dataframe(df):
    """
    Applies deduplication using window functions to keep only the newest records
    and parses string dates into structured timestamps.
    """
    # Convert string date to timestamp
    df_trans = df.withColumn("date_posted", to_timestamp(col("date_raw"), "yyyy-MM-dd'T'HH:mm:ssXXX"))
    df_trans = df_trans.drop("date_raw")
    
    # Derive geography parsing fields
    df_trans = df_trans.withColumn(
        "remote_flag",
        when(col("location").rlike("(?i)remote"), True).otherwise(False)
    ).withColumn(
        "country",
        when(col("remote_flag") == True, lit("Remote"))
        .when(col("location").rlike("(?i)canada"), lit("Canada"))
        .when(col("location").rlike("(?i)usa|united states|america"), lit("USA"))
        .when(col("location").rlike("(?i)uk|united kingdom|london"), lit("UK"))
        .when(col("location").isNull() | (trim(col("location")) == ""), lit("Unknown"))
        .otherwise(col("location"))
    ).withColumn(
        "region",
        when(col("remote_flag") == True, lit("Remote"))
        .when(col("location").rlike("(?i)hybrid"), lit("hybrid"))
        .otherwise(lit("onsite"))
    )
    
    # Window specification to find duplicates based on ID, ordering by epoch descending
    windowSpec = Window.partitionBy("id").orderBy(desc("epoch"))
    df_ranked = df_trans.withColumn("row_num", row_number().over(windowSpec))
    
    # Deduplicate: Keep newest (row_num == 1) for Silver, mark rest as duplicate in Quarantine
    df_silver = df_ranked.filter(col("row_num") == 1).drop("row_num")
    df_duplicates = df_ranked.filter(col("row_num") > 1) \
                             .withColumn("reason", lit("duplicate")) \
                             .drop("row_num")
                             
    return df_silver, df_duplicates

def get_s3_prefix_size_bytes(s3_client, bucket: str, prefix: str) -> int:
    """
    Lists S3 objects under a prefix and computes the total file size in bytes.
    """
    size_bytes = 0
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                size_bytes += obj['Size']
    except Exception as e:
        print(f"Error calculating S3 prefix size: {e}")
    return size_bytes

def main():
    # Retrieve job arguments
    # Job Bookmarks and script deployment args are resolved here
    args = getResolvedOptions(sys.argv, ['JOB_NAME', 'pipeline_execution_id', 's3_bucket'])
    
    pipeline_execution_id = args['pipeline_execution_id']
    s3_bucket = args['s3_bucket']
    
    # Initialize AWS Glue and Spark contexts
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
    
    print(f"Starting Silver ETL Job Run (Execution ID: {pipeline_execution_id})")
    start_time = time.perf_counter()
    
    # 1. Read raw Bronze data via Glue Data Catalog
    print("Reading Bronze table from Glue Catalog...")
    bronze_dyf = glueContext.create_dynamic_frame.from_catalog(
        database="cp_dev_catalog",
        table_name="source_remoteok",
        transformation_ctx="bronze_source"
    )
    bronze_df = bronze_dyf.toDF()
    
    if bronze_df.count() == 0:
        print("No new Bronze records found. Completing job run.")
        job.commit()
        return

    # 2. Stage 1: Schema Validation
    print("Running Schema Validation stage...")
    df_schema_validated = validate_schema(bronze_df)
    
    # 3. Stage 2: Business Rules Evaluation
    print("Running Business Validation stage...")
    df_business_validated = validate_business_rules(df_schema_validated)
    
    # Separate valid and invalid records
    df_invalid = df_business_validated.filter(col("reason").isNotNull())
    df_valid_rules = df_business_validated.filter(col("reason").isNull())
    
    # 4. Stage 3: Data Cleaning
    print("Running Data Cleaning stage...")
    df_cleaned = clean_dataframe(df_valid_rules)
    
    # 5. Stage 4: Transformations & Deduplication
    print("Running Transformations and Deduplication stage...")
    df_silver, df_duplicates = transform_dataframe(df_cleaned)
    
    # Gather operational KPIs
    input_records = df_schema_validated.count()
    output_records = df_silver.count()
    rejected_records = df_invalid.count()
    duplicate_records = df_duplicates.count()
    
    # Calculate salary metrics
    jobs_with_salary = df_silver.filter(col("salary_min").isNotNull() | col("salary_max").isNotNull()).count()
    jobs_without_salary = df_silver.filter(col("salary_min").isNull() & col("salary_max").isNull()).count()
    
    # Log duplicate IDs
    if duplicate_records > 0:
        duplicate_ids_rows = df_duplicates.select("id").distinct().collect()
        duplicate_ids = [row["id"] for row in duplicate_ids_rows]
        print(f"Duplicate Job IDs identified and quarantined: {duplicate_ids}")
    
    # Build complete Quarantine DataFrame
    df_quarantine = df_invalid.unionByName(df_duplicates, allowMissingColumns=True)
    
    # Ensure correct column projection for Silver table
    df_silver_final = df_silver.select([col(field.name) for field in SILVER_SCHEMA.fields])
    
    # 6. Write Silver dataset (Snappy compressed Parquet)
    silver_path = f"s3://{s3_bucket}/silver/source=remoteok/"
    print(f"Writing {output_records} records to Silver path: {silver_path}")
    df_silver_final.write \
        .mode("append") \
        .partitionBy("year", "month", "day") \
        .parquet(silver_path, compression="snappy")
        
    # 7. Write Quarantine dataset (JSON format)
    quarantine_path = f"s3://{s3_bucket}/quarantine/source=remoteok/"
    quarantine_records_count = df_quarantine.count()
    if quarantine_records_count > 0:
        print(f"Writing {quarantine_records_count} records to Quarantine path: {quarantine_path}")
        df_quarantine.write \
            .mode("append") \
            .partitionBy("reason", "year", "month", "day") \
            .json(quarantine_path)
            
    # Calculate output file sizes in S3
    s3_client = boto3.client("s3")
    silver_prefix = "silver/source=remoteok/"
    output_size_bytes = get_s3_prefix_size_bytes(s3_client, s3_bucket, silver_prefix)
    
    # 8. Write Operational Metadata
    processing_duration_ms = int((time.perf_counter() - start_time) * 1000.0)
    metadata_payload = {
        "input_records": input_records,
        "output_records": output_records,
        "rejected_records": rejected_records,
        "duplicate_records": duplicate_records,
        "jobs_with_salary": jobs_with_salary,
        "jobs_without_salary": jobs_without_salary,
        "validation_failure_count": rejected_records + duplicate_records,
        "processing_duration_ms": processing_duration_ms,
        "output_size_bytes": output_size_bytes,
        "schema_version": "1.0",
        "pipeline_execution_id": pipeline_execution_id,
        "transformation_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    metadata_key = f"metadata/silver_etl/{pipeline_execution_id}.metadata.json"
    print(f"Uploading operational metadata to: s3://{s3_bucket}/{metadata_key}")
    s3_client.put_object(
        Bucket=s3_bucket,
        Key=metadata_key,
        Body=json.dumps(metadata_payload, indent=2),
        ContentType="application/json"
    )
    
    # Commit AWS Glue Job Bookmark state
    job.commit()
    print("Silver ETL Job completed successfully.")

if __name__ == "__main__":
    main()
