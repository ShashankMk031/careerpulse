"""
AWS Glue Silver ETL Job deployment and execution automation script for CareerPulse.
Responsible for:
- Uploading the 'silver_etl.py' PySpark script to the script path in S3.
- Creating or updating the Glue Job 'cp_dev_silver_etl' in the catalog.
- Initiating a job run with unique pipeline execution parameters.
- Polling the job execution until terminal state is achieved.
"""

import sys
import os
import time
import uuid
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

# Configuration
AWS_REGION = "ap-south-1"
S3_BUCKET = "cp-dev-datalake-321422008826"
JOB_NAME = "cp_dev_silver_etl"
IAM_ROLE_NAME = "cp-dev-glue-role"
LOCAL_SCRIPT_PATH = "glue_jobs/silver_etl.py"
S3_SCRIPT_PATH = f"s3://{S3_BUCKET}/scripts/silver_etl.py"
S3_TEMP_PATH = f"s3://{S3_BUCKET}/temporary/"

def get_role_arn(iam_client, role_name: str) -> str:
    try:
        response = iam_client.get_role(RoleName=role_name)
        return response["Role"]["Arn"]
    except ClientError as e:
        print(f"Error fetching IAM Role {role_name}: {e}")
        sys.exit(1)

def upload_script_to_s3(s3_client, local_path: str, bucket: str, key: str) -> None:
    try:
        print(f"Uploading script {local_path} to s3://{bucket}/{key}...")
        s3_client.upload_file(local_path, bucket, key)
        print("Script upload complete.")
    except Exception as e:
        print(f"Error uploading script to S3: {e}")
        sys.exit(1)

def main() -> None:
    print("Initializing AWS clients...")
    session = boto3.Session(region_name=AWS_REGION)
    glue_client = session.client("glue")
    iam_client = session.client("iam")
    s3_client = session.client("s3")
    
    # 1. Fetch Glue Role ARN
    role_arn = get_role_arn(iam_client, IAM_ROLE_NAME)
    print(f"Found Role ARN: {role_arn}")
    
    # 2. Upload script to S3
    script_s3_key = "scripts/silver_etl.py"
    upload_script_to_s3(s3_client, LOCAL_SCRIPT_PATH, S3_BUCKET, script_s3_key)
    
    # 3. Create or Update Glue Job
    job_command = {
        "Name": "glueetl",
        "ScriptLocation": S3_SCRIPT_PATH,
        "PythonVersion": "3"
    }
    
    default_args = {
        "--job-bookmark-option": "job-bookmark-enable",
        "--TempDir": S3_TEMP_PATH,
        "--s3_bucket": S3_BUCKET,
        "--enable-metrics": "true",
        "--enable-continuous-cloudwatch-log": "true"
    }
    
    print(f"Creating/updating AWS Glue Job: {JOB_NAME}...")
    try:
        glue_client.create_job(
            Name=JOB_NAME,
            Description="Silver Layer PySpark ETL job with validation, cleaning, and window-based deduplication",
            Role=role_arn,
            ExecutionProperty={
                "MaxConcurrentRuns": 1
            },
            Command=job_command,
            DefaultArguments=default_args,
            GlueVersion="5.0",
            WorkerType="G.1X",
            NumberOfWorkers=2,
            Timeout=10
        )
        print(f"Successfully created Glue Job: {JOB_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "AlreadyExistsException":
            print(f"Glue Job {JOB_NAME} already exists, updating configuration...")
            try:
                glue_client.update_job(
                    JobName=JOB_NAME,
                    JobUpdate={
                        "Role": role_arn,
                        "ExecutionProperty": {
                            "MaxConcurrentRuns": 1
                        },
                        "Command": job_command,
                        "DefaultArguments": default_args,
                        "GlueVersion": "5.0",
                        "WorkerType": "G.1X",
                        "NumberOfWorkers": 2,
                        "Timeout": 10
                    }
                )
                print(f"Successfully updated Glue Job: {JOB_NAME}")
            except ClientError as ue:
                print(f"Error updating Glue Job: {ue}")
                sys.exit(1)
        else:
            print(f"Error creating Glue Job: {e}")
            sys.exit(1)
            
    # 4. Start Glue Job Run
    execution_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pipeline_execution_id = f"{execution_ts}-{uuid.uuid4().hex[:6]}"
    print(f"Starting Glue Job run (Execution ID: {pipeline_execution_id})...")
    
    try:
        run_response = glue_client.start_job_run(
            JobName=JOB_NAME,
            Arguments={
                "--pipeline_execution_id": pipeline_execution_id
            }
        )
        run_id = run_response["JobRunId"]
        print(f"Glue Job run started with Run ID: {run_id}")
    except ClientError as e:
        print(f"Error starting Glue Job run: {e}")
        sys.exit(1)
        
    # 5. Poll Job Run status
    print("Waiting for Glue Job run to complete...")
    while True:
        try:
            status_response = glue_client.get_job_run(JobName=JOB_NAME, RunId=run_id)
            run_status = status_response["JobRun"]["JobRunState"]
            print(f"Current Job Run State: {run_status}")
            
            if run_status in ("SUCCEEDED", "FAILED", "STOPPED", "TIMEOUT"):
                if run_status == "SUCCEEDED":
                    print("Glue Job completed successfully!")
                else:
                    error_msg = status_response["JobRun"].get("ErrorMessage", "Unknown error")
                    print(f"Glue Job failed/stopped. Terminal State: {run_status}. Error: {error_msg}")
                    sys.exit(1)
                break
        except ClientError as e:
            print(f"Error checking job run status: {e}")
            
        time.sleep(15)
        
    print("Glue Silver ETL deployment and run execution pipeline complete.")

if __name__ == "__main__":
    main()
