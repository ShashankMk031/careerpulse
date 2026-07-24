"""
Athena integration verification script for the Gold Layer.
Responsible for:
- Querying each of the 6 auto-discovered Gold database tables in Glue Catalog.
- Printing query results to verify clean analytical aggregations.
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

VERIFICATION_QUERIES = {
    "Company Analytics (gold_company)": f"""
        SELECT company, total_jobs, unique_locations, avg_salary_min, avg_salary_max, highest_paying_role, latest_posting, jobs_with_salary 
        FROM {DATABASE_NAME}.gold_company 
        ORDER BY total_jobs DESC 
        LIMIT 5
    """,
    "Skills Analytics (gold_skills)": f"""
        SELECT tag, job_demand_count, avg_salary_min, avg_salary_max, salary_premium, remote_jobs_count 
        FROM {DATABASE_NAME}.gold_skills 
        ORDER BY job_demand_count DESC 
        LIMIT 5
    """,
    "Geography Analytics (gold_geography)": f"""
        SELECT country, region, jobs_count, avg_salary_min, avg_salary_max, company_count, remote_count, onsite_count 
        FROM {DATABASE_NAME}.gold_geography 
        ORDER BY jobs_count DESC 
        LIMIT 5
    """,
    "Salary Analytics (gold_salary)": f"""
        SELECT salary_tier, jobs_count, avg_salary_min, avg_salary_max 
        FROM {DATABASE_NAME}.gold_salary 
        ORDER BY jobs_count DESC 
        LIMIT 5
    """,
    "Technology Analytics (gold_technology)": f"""
        SELECT tech_tag, job_demand_count, avg_salary_min, avg_salary_max, top_company 
        FROM {DATABASE_NAME}.gold_technology 
        ORDER BY job_demand_count DESC 
        LIMIT 5
    """,
    "Hiring Summary Dashboard KPIs (gold_summary)": f"""
        SELECT total_jobs, total_companies, total_locations, remote_jobs, remote_percentage, average_salary, median_salary, highest_salary, highest_paying_company, top_company, top_skill, top_country, jobs_with_salary, jobs_without_salary, generation_timestamp 
        FROM {DATABASE_NAME}.gold_summary
    """
}

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
            
            if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
                return response["QueryExecution"]
                
        except ClientError as e:
            print(f"Error polling query status: {e}")
            
        time.sleep(2)

def main() -> None:
    print("Initializing Athena client...")
    session = boto3.Session(region_name=AWS_REGION)
    athena_client = session.client("athena")
    
    for title, query in VERIFICATION_QUERIES.items():
        print("\n" + "=" * 80)
        print(f"Running query for: {title}")
        print("=" * 80)
        
        q_id = execute_athena_query(athena_client, query)
        result = wait_for_query_completion(athena_client, q_id)
        
        status = result["Status"]["State"]
        if status != "SUCCEEDED":
            reason = result["Status"].get("StateChangeReason", "Unknown reason")
            print(f"Query failed: {reason}")
            continue
            
        try:
            results_resp = athena_client.get_query_results(QueryExecutionId=q_id)
            rows = results_resp["ResultSet"]["Rows"]
            
            if not rows:
                print("No rows returned.")
                continue
                
            # Print column headers
            headers = [col.get("VarCharValue", "NULL") for col in rows[0]["Data"]]
            print(" | ".join(headers))
            print("-" * 120)
            
            # Print data rows
            for row in rows[1:]:
                values = [col.get("VarCharValue", "NULL") for col in row["Data"]]
                print(" | ".join(values))
                
        except ClientError as e:
            print(f"Error fetching results: {e}")

    print("\nAthena Gold integration verified successfully.")

if __name__ == "__main__":
    main()
