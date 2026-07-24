"""
CareerPulse Gold Layer PySpark ETL Script.
Orchestrates the generation of 6 Gold analytical datasets:
- Company Analytics
- Skills Analytics
- Geography Analytics
- Salary Analytics
- Technology Analytics
- Hiring Summary (Dashboard KPIs)

Outputs are written separately under gold/ in S3 as partitioned Parquet with Snappy compression.
"""

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
from pyspark.sql.functions import col, count, count_distinct, avg, sum, when, lit, desc, max, coalesce, explode, array_distinct, trim, lower, current_timestamp, struct, rlike, percentile_approx
from pyspark.sql.types import StructType, StructField, StringType, LongType, IntegerType, BooleanType, TimestampType

# Configurable salary buckets for Salary Analytics
SALARY_BUCKETS = [
    ("Entry (< 50k)", 0, 50000),
    ("Mid (50k-100k)", 50000, 100000),
    ("Senior (100k-150k)", 100000, 150000),
    ("Staff (150k+)", 150000, 9999999)
]

def generate_company_analytics(df):
    """
    Groups valid Silver records by company to compute metrics like job posting counts,
    average salaries, highest paying role, and latest posting dates.
    """
    # Struct aggregation is used to safely fetch position associated with maximum salary_max
    company_df = df.groupBy("company").agg(
        count(lit(1)).alias("total_jobs"),
        count_distinct("location").alias("unique_locations"),
        avg("salary_min").alias("avg_salary_min"),
        avg("salary_max").alias("avg_salary_max"),
        sum(when(col("original") == True, lit(1)).otherwise(lit(0))).alias("original_jobs_count"),
        coalesce(max(struct(col("salary_max").alias("salary"), col("position").alias("role")))["role"], lit("Unknown")).alias("highest_paying_role"),
        max("date_posted").alias("latest_posting"),
        sum(when(col("salary_min").isNotNull() | col("salary_max").isNotNull(), lit(1)).otherwise(lit(0))).alias("jobs_with_salary")
    )
    return company_df

def generate_skills_analytics(df, overall_avg_max_salary):
    """
    Explodes the tags column to compute developer skill demand, location splits,
    average salaries, and the premium earned over the market average.
    """
    # Distinct tags to prevent duplicate tags within the same job from inflating job counts
    df_distinct_tags = df.withColumn("tags", array_distinct(col("tags")))
    df_exploded = df_distinct_tags.select(explode("tags").alias("tag"), "salary_min", "salary_max", "location")
    
    # Trim and normalize tags
    df_exploded = df_exploded.withColumn("tag", lower(trim(col("tag"))))
    
    # Filter out empty tags
    df_exploded = df_exploded.filter(col("tag") != "")
    
    skills_df = df_exploded.groupBy("tag").agg(
        count(lit(1)).alias("job_demand_count"),
        avg("salary_min").alias("avg_salary_min"),
        avg("salary_max").alias("avg_salary_max"),
        sum(when(col("location").rlike("(?i)remote"), lit(1)).otherwise(lit(0))).alias("remote_jobs_count")
    )
    
    # Calculate salary premium: difference between the skill's average salary_max and the overall average
    skills_df = skills_df.withColumn("salary_premium", col("avg_salary_max") - lit(overall_avg_max_salary))
    
    return skills_df

def generate_geography_analytics(df):
    """
    Aggregates metrics per country/region utilizing normalized fields from Silver.
    """
    geography_df = df.groupBy("country", "region").agg(
        count(lit(1)).alias("jobs_count"),
        avg("salary_min").alias("avg_salary_min"),
        avg("salary_max").alias("avg_salary_max"),
        count_distinct("company").alias("company_count"),
        sum(when(col("remote_flag") == True, lit(1)).otherwise(lit(0))).alias("remote_count"),
        sum(when((col("remote_flag") == False) & (col("region") != "hybrid"), lit(1)).otherwise(lit(0))).alias("onsite_count"),
        sum(when(col("region") == "hybrid", lit(1)).otherwise(lit(0))).alias("hybrid_count")
    )
    return geography_df


def generate_salary_analytics(df):
    """
    Groups job listings into dynamic, configurable salary tiers.
    """
    # Construct conditional 'when' expressions dynamically
    expr = when(col("salary_max").isNull(), lit("Not Specified"))
    for tier_name, min_val, max_val in SALARY_BUCKETS:
        expr = expr.when((col("salary_max") >= min_val) & (col("salary_max") < max_val), lit(tier_name))
    expr = expr.otherwise(lit("Other"))
    
    df_tiered = df.withColumn("salary_tier", expr)
    
    salary_df = df_tiered.groupBy("salary_tier").agg(
        count(lit(1)).alias("jobs_count"),
        avg("salary_min").alias("avg_salary_min"),
        avg("salary_max").alias("avg_salary_max")
    )
    return salary_df

def generate_technology_analytics(df):
    """
    Explodes job tags and identifies average salaries alongside the top hiring company
    for each software technology.
    """
    df_distinct_tags = df.withColumn("tags", array_distinct(col("tags")))
    df_exploded = df_distinct_tags.select(explode("tags").alias("tag"), "salary_min", "salary_max", "company")
    df_exploded = df_exploded.withColumn("tag", lower(trim(col("tag")))).filter(col("tag") != "")
    
    # Calculate company job counts per tag
    df_company_counts = df_exploded.groupBy("tag", "company").agg(count(lit(1)).alias("job_count"))
    
    # Identify top company offering the most roles per tag using struct aggregation
    df_top_company = df_company_counts.groupBy("tag").agg(
        coalesce(max(struct(col("job_count").alias("jobs"), col("company").alias("name")))["name"], lit("Unknown")).alias("top_company")
    )
    
    # Compute technology demand metrics
    tech_base_df = df_exploded.groupBy("tag").agg(
        count(lit(1)).alias("job_demand_count"),
        avg("salary_min").alias("avg_salary_min"),
        avg("salary_max").alias("avg_salary_max")
    )
    
    # Join top hiring company back into base metrics
    technology_df = tech_base_df.join(df_top_company, "tag", "left").withColumnRenamed("tag", "tech_tag")
    return technology_df

def generate_hiring_summary(df):
    """
    Generates high-level landing page dashboard KPI metrics.
    """
    total_jobs = df.count()
    if total_jobs == 0:
        return None
        
    # Calculate top company
    company_row = df.groupBy("company").count().orderBy(desc("count")).first()
    top_company = company_row["company"] if company_row else "Unknown"
    
    # Calculate top skill
    df_distinct_tags = df.withColumn("tags", array_distinct(col("tags")))
    df_exploded = df_distinct_tags.select(explode("tags").alias("tag"))
    df_exploded = df_exploded.withColumn("tag", lower(trim(col("tag")))).filter(col("tag") != "")
    skill_row = df_exploded.groupBy("tag").count().orderBy(desc("count")).first()
    top_skill = skill_row["tag"] if skill_row else "Unknown"
    
    # Calculate top country
    country_row = df.filter((col("country") != "Remote") & (col("country").isNotNull()) & (trim(col("country")) != "")).groupBy("country").count().orderBy(desc("count")).first()
    top_country = country_row["country"] if country_row else "Unknown"
    
    # Run aggregations
    summary_df = df.groupBy().agg(
        count(lit(1)).alias("total_jobs"),
        count_distinct("company").alias("total_companies"),
        count_distinct("location").alias("total_locations"),
        sum(when(col("remote_flag") == True, lit(1)).otherwise(lit(0))).alias("remote_jobs"),
        avg((col("salary_min") + col("salary_max")) / 2).alias("average_salary"),
        percentile_approx((col("salary_min") + col("salary_max")) / 2, lit(0.5)).alias("median_salary"),
        max("salary_max").alias("highest_salary"),
        coalesce(max(struct(col("salary_max").alias("salary"), col("company").alias("name")))["name"], lit("Unknown")).alias("highest_paying_company"),
        sum(when(col("salary_min").isNotNull() | col("salary_max").isNotNull(), lit(1)).otherwise(lit(0))).alias("jobs_with_salary"),
        sum(when(col("salary_min").isNull() & col("salary_max").isNull(), lit(1)).otherwise(lit(0))).alias("jobs_without_salary")
    )
    
    # Add remote percentage and timestamp columns
    summary_df = summary_df.withColumn("top_company", lit(top_company)) \
                           .withColumn("top_skill", lit(top_skill)) \
                           .withColumn("top_country", lit(top_country)) \
                           .withColumn("remote_percentage", (col("remote_jobs") / col("total_jobs")) * 100.0) \
                           .withColumn("generation_timestamp", current_timestamp())
                           
    return summary_df

def get_s3_prefix_size_bytes(s3_client, bucket: str, prefix: str) -> int:
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
    # Resolve command-line arguments
    args = getResolvedOptions(sys.argv, ['JOB_NAME', 'pipeline_execution_id', 's3_bucket'])
    pipeline_execution_id = args['pipeline_execution_id']
    s3_bucket = args['s3_bucket']
    
    # Initialize AWS Glue context
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
    
    print(f"Starting Gold Layer ETL Job Run (Execution ID: {pipeline_execution_id})")
    
    # 1. Read from Silver catalog table
    print("Reading remoteok_silver table from Glue Catalog...")
    silver_dyf = glueContext.create_dynamic_frame.from_catalog(
        database="cp_dev_catalog",
        table_name="remoteok_silver",
        transformation_ctx="silver_source"
    )
    silver_df = silver_dyf.toDF()
    
    input_records = silver_df.count()
    if input_records == 0:
        print("No new Silver records found. Completing job run.")
        job.commit()
        return
        
    s3_client = boto3.client("s3")
    
    # Compute overall average max salary for skills salary premium
    overall_avg_max_salary = silver_df.agg(coalesce(avg("salary_max"), lit(0.0))).collect()[0][0]
    print(f"Overall average max salary: {overall_avg_max_salary}")
    
    # Define datasets dictionary for dynamic processing loops
    datasets = {
        "company": lambda: generate_company_analytics(silver_df),
        "skills": lambda: generate_skills_analytics(silver_df, overall_avg_max_salary),
        "geography": lambda: generate_geography_analytics(silver_df),
        "salary": lambda: generate_salary_analytics(silver_df),
        "technology": lambda: generate_technology_analytics(silver_df),
        "summary": lambda: generate_hiring_summary(silver_df)
    }
    
    for name, generator in datasets.items():
        print(f"Generating Gold dataset: {name}...")
        start_time = time.perf_counter()
        
        # Run transformation
        gold_df = generator()
        if gold_df is None:
            print(f"Dataset {name} generated empty output, skipping.")
            continue
            
        output_records = gold_df.count()
        gold_path = f"s3://{s3_bucket}/gold/{name}/"
        print(f"Writing {output_records} records to: {gold_path}")
        
        # Write dataset to S3 in Parquet format with Snappy compression
        gold_df.write \
            .mode("overwrite") \
            .parquet(gold_path, compression="snappy")
            
        # Compute output metrics
        processing_duration_ms = int((time.perf_counter() - start_time) * 1000.0)
        output_prefix = f"gold/{name}/"
        output_size_bytes = get_s3_prefix_size_bytes(s3_client, s3_bucket, output_prefix)
        
        # Write S3 metadata metrics separately per dataset
        metadata_payload = {
            "input_records": input_records,
            "output_records": output_records,
            "processing_duration_ms": processing_duration_ms,
            "output_size_bytes": output_size_bytes,
            "pipeline_execution_id": pipeline_execution_id,
            "generation_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        metadata_key = f"metadata/gold/{name}/{pipeline_execution_id}.metadata.json"
        print(f"Uploading metadata for {name} to: s3://{s3_bucket}/{metadata_key}")
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=metadata_key,
            Body=json.dumps(metadata_payload, indent=2),
            ContentType="application/json"
        )
        
    job.commit()
    print("Gold Layer ETL Job completed successfully.")

if __name__ == "__main__":
    main()
