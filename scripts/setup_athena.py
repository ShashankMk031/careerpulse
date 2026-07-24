
"""
Athena Integration setup script for CareerPulse.
Responsible for:
- Configuring the Athena query results location in S3.
- Creating the 'remoteok_bronze' flattened view over the raw nested 'source_remoteok' table.
- Running a verification query and printing the results.
"""

import sys
import time
import boto3
from botocore.exceptions import ClientError

# Configuration
AWS_REGION = "ap-south-1"
DATABASE_NAME = "cp_dev_catalog"
ATHENA_OUTPUT_LOCATION = "s3://cp-dev-datalake-321422008826/athena-results/"

# Define the VIEW creation query. Unnesting the nested array allows Athena queries to work
# exactly like flat tabular databases.
VIEW_QUERY = f"""
CREATE OR REPLACE VIEW {DATABASE_NAME}.remoteok_bronze AS
SELECT
    job.slug,
    job.id,
    job.epoch,
    job.date,
    job.company,
    job.company_logo,
    job.position,
    job.tags,
    job.description,
    job.location,
    job.apply_url,
    job.salary_min,
    job.salary_max,
    job.logo,
    job.url,
    job.original,
    year,
    month,
    day
FROM
    {DATABASE_NAME}.source_remoteok
CROSS JOIN
    UNNEST(array) as t(job)
"""

SELECT_QUERY = f"SELECT id, company, position, location, year, month, day FROM {DATABASE_NAME}.remoteok_bronze LIMIT 10"

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
    
    # 1. Create the View
    print("Creating Athena View 'remoteok_bronze'...")
    q_id = execute_athena_query(athena_client, VIEW_QUERY)
    result = wait_for_query_completion(athena_client, q_id)
    
    status = result["Status"]["State"]
    if status != "SUCCEEDED":
        reason = result["Status"].get("StateChangeReason", "Unknown reason")
        print(f"Failed to create View: {reason}")
        sys.exit(1)
    print("Successfully created Athena view 'remoteok_bronze'.")
    
    # 2. Run verification query
    print("Running verification SELECT query on 'remoteok_bronze'...")
    select_q_id = execute_athena_query(athena_client, SELECT_QUERY)
    select_result = wait_for_query_completion(athena_client, select_q_id)
    
    select_status = select_result["Status"]["State"]
    if select_status != "SUCCEEDED":
        reason = select_result["Status"].get("StateChangeReason", "Unknown reason")
        print(f"Verification query failed: {reason}")
        sys.exit(1)
        
    # 3. Retrieve and print results
    print("Retrieving query results:")
    try:
        results_resp = athena_client.get_query_results(QueryExecutionId=select_q_id)
        rows = results_resp["ResultSet"]["Rows"]
        
        # Print column headers
        headers = [col["VarCharValue"] for col in rows[0]["Data"]]
        print(f" | ".join(headers))
        print("-" * 80)
        
        # Print data rows
        for row in rows[1:]:
            values = [col.get("VarCharValue", "NULL") for col in row["Data"]]
            print(f" | ".join(values))
            
    except ClientError as e:
        print(f"Error fetching results: {e}")
        sys.exit(1)

    print("Athena integration verified successfully.")

if __name__ == "__main__":
    main()
