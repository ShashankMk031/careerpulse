"""
Athena integration setup and verification script for the Silver Layer.
Responsible for:
- Creating the explicit DDL table 'remoteok_silver' in the Glue Catalog database.
- Executing MSCK REPAIR TABLE to recover S3 partition mappings.
- Running a test SELECT query to verify tabular Parquet rows can be queried successfully.
"""

import sys
import time
import boto3
from botocore.exceptions import ClientError

# Configuration
AWS_REGION = "ap-south-1"
DATABASE_NAME = "cp_dev_catalog"
S3_BUCKET = "cp-dev-datalake-321422008826"
ATHENA_OUTPUT_LOCATION = f"s3://{S3_BUCKET}/athena-results/"

DROP_QUERY = f"DROP TABLE IF EXISTS {DATABASE_NAME}.remoteok_silver"

# Explicit DDL for Silver Layer Parquet table
DDL_QUERY = f"""
CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE_NAME}.remoteok_silver (
    id bigint,
    slug string,
    epoch bigint,
    date_posted timestamp,
    company string,
    company_logo string,
    position string,
    tags array<string>,
    description string,
    location string,
    country string,
    region string,
    remote_flag boolean,
    apply_url string,
    salary_min int,
    salary_max int,
    logo string,
    url string,
    original boolean
)
PARTITIONED BY (
    year string,
    month string,
    day string
)
STORED AS PARQUET
LOCATION 's3://{S3_BUCKET}/silver/source=remoteok/'
TBLPROPERTIES ('parquet.compress'='SNAPPY')
"""

REPAIR_QUERY = f"MSCK REPAIR TABLE {DATABASE_NAME}.remoteok_silver"

SELECT_QUERY = f"""
SELECT id, company, position, date_posted, country, region, remote_flag, salary_min, salary_max, year, month, day 
FROM {DATABASE_NAME}.remoteok_silver 
LIMIT 10
"""

def execute_athena_query(athena_client, query_string: str) -> str:
    try:
        response = athena_client.start_query_execution(
            QueryString=query_string,
            QueryExecutionContext={"Database": DATABASE_NAME},
            ResultConfiguration={"OutputLocation": ATHENA_OUTPUT_LOCATION}
        )
        return response["QueryExecutionId"]
    except ClientError as e:
        print(f"Error starting query execution: {e}")
        sys.exit(1)

def wait_for_query_completion(athena_client, query_execution_id: str) -> dict:
    while True:
        try:
            response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            state = response["QueryExecution"]["Status"]["State"]
            print(f"Query {query_execution_id} State: {state}")
            
            if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
                return response["QueryExecution"]
                
        except ClientError as e:
            print(f"Error polling query status: {e}")
            
        time.sleep(3)

def main() -> None:
    print("Initializing Athena client...")
    session = boto3.Session(region_name=AWS_REGION)
    athena_client = session.client("athena")
    
    # Drop existing table to update the schema
    print("Dropping existing Athena Table 'remoteok_silver' if exists...")
    drop_q_id = execute_athena_query(athena_client, DROP_QUERY)
    wait_for_query_completion(athena_client, drop_q_id)
    
    # 1. Create External Table
    print("Creating Athena External Table 'remoteok_silver'...")
    q_id = execute_athena_query(athena_client, DDL_QUERY)
    result = wait_for_query_completion(athena_client, q_id)
    
    status = result["Status"]["State"]
    if status != "SUCCEEDED":
        reason = result["Status"].get("StateChangeReason", "Unknown reason")
        print(f"Failed to create Table: {reason}")
        sys.exit(1)
    print("Successfully created Athena table 'remoteok_silver'.")
    
    # 2. Repair Table Partitions
    print("Repairing partition keys (discovering new partitions in S3)...")
    repair_q_id = execute_athena_query(athena_client, REPAIR_QUERY)
    repair_result = wait_for_query_completion(athena_client, repair_q_id)
    
    repair_status = repair_result["Status"]["State"]
    if repair_status != "SUCCEEDED":
        reason = repair_result["Status"].get("StateChangeReason", "Unknown reason")
        print(f"Failed to repair partitions: {reason}")
        sys.exit(1)
    print("Successfully loaded partitions into catalog.")
    
    # 3. Run verification SELECT query
    print("Running verification SELECT query on 'remoteok_silver'...")
    select_q_id = execute_athena_query(athena_client, SELECT_QUERY)
    select_result = wait_for_query_completion(athena_client, select_q_id)
    
    select_status = select_result["Status"]["State"]
    if select_status != "SUCCEEDED":
        reason = select_result["Status"].get("StateChangeReason", "Unknown reason")
        print(f"Verification query failed: {reason}")
        sys.exit(1)
        
    # 4. Retrieve and print results
    print("Retrieving query results:")
    try:
        results_resp = athena_client.get_query_results(QueryExecutionId=select_q_id)
        rows = results_resp["ResultSet"]["Rows"]
        
        # Print column headers
        headers = [col["VarCharValue"] for col in rows[0]["Data"]]
        print(f" | ".join(headers))
        print("-" * 120)
        
        # Print data rows
        for row in rows[1:]:
            values = [col.get("VarCharValue", "NULL") for col in row["Data"]]
            print(f" | ".join(values))
            
    except ClientError as e:
        print(f"Error fetching results: {e}")
        sys.exit(1)

    print("Athena Silver integration verified successfully.")

if __name__ == "__main__":
    main()
