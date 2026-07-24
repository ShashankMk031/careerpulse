"""
Glue Deployment automation script for CareerPulse.
Responsible for:
- Creating the Glue Database 'cp_dev_catalog' if not exists.
- Creating/updating the Glue Crawler 'cp_dev_bronze_crawler'.
- Starting the crawler run and polling until completion.
"""

import sys
import time
import boto3
from botocore.exceptions import ClientError

# Configuration
AWS_REGION = "ap-south-1"
DATABASE_NAME = "cp_dev_catalog"
CRAWLER_NAME = "cp_dev_bronze_crawler"
IAM_ROLE_NAME = "cp-dev-glue-role"
S3_TARGET_PATH = "s3://cp-dev-datalake-321422008826/bronze/source=remoteok/"

def get_role_arn(iam_client, role_name: str) -> str:
    try:
        response = iam_client.get_role(RoleName=role_name)
        return response["Role"]["Arn"]
    except ClientError as e:
        print(f"Error fetching IAM Role {role_name}: {e}")
        sys.exit(1)

def main() -> None:
    print("Initializing AWS clients...")
    session = boto3.Session(region_name=AWS_REGION)
    glue_client = session.client("glue")
    iam_client = session.client("iam")
    
    role_arn = get_role_arn(iam_client, IAM_ROLE_NAME)
    print(f"Found Glue Role ARN: {role_arn}")
    
    # 1. Create Glue Database
    print(f"Creating/verifying Glue Database: {DATABASE_NAME}...")
    try:
        glue_client.create_database(
            DatabaseInput={
                "Name": DATABASE_NAME,
                "Description": "Metadata catalog for CareerPulse datalake layers"
            }
        )
        print(f"Successfully created database: {DATABASE_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "AlreadyExistsException":
            print(f"Database {DATABASE_NAME} already exists.")
        else:
            print(f"Error creating database: {e}")
            sys.exit(1)
            
    # 2. Create or Update Crawler
    print(f"Creating/verifying Glue Crawler: {CRAWLER_NAME}...")
    crawler_targets = {
        "S3Targets": [
            {
                "Path": S3_TARGET_PATH,
                "Exclusions": ["**/*.metadata.json"]
            }
        ]
    }
    
    try:
        glue_client.create_crawler(
            Name=CRAWLER_NAME,
            Role=role_arn,
            DatabaseName=DATABASE_NAME,
            Targets=crawler_targets,
            Description="Crawler for RemoteOK Bronze dataset partitioned by year/month/day",
            SchemaChangePolicy={
                "UpdateBehavior": "UPDATE_IN_DATABASE",
                "DeleteBehavior": "DEPRECATE_IN_DATABASE"
            }
        )
        print(f"Successfully created crawler: {CRAWLER_NAME}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "AlreadyExistsException":
            print(f"Crawler {CRAWLER_NAME} already exists, updating configuration...")
            try:
                glue_client.update_crawler(
                    Name=CRAWLER_NAME,
                    Role=role_arn,
                    DatabaseName=DATABASE_NAME,
                    Targets=crawler_targets,
                    Description="Crawler for RemoteOK Bronze dataset partitioned by year/month/day",
                    SchemaChangePolicy={
                        "UpdateBehavior": "UPDATE_IN_DATABASE",
                        "DeleteBehavior": "DEPRECATE_IN_DATABASE"
                    }
                )
                print(f"Successfully updated crawler: {CRAWLER_NAME}")
            except ClientError as ue:
                print(f"Error updating crawler: {ue}")
                sys.exit(1)
        else:
            print(f"Error creating crawler: {e}")
            sys.exit(1)
            
    # 3. Start Crawler run
    print(f"Starting crawler: {CRAWLER_NAME}...")
    try:
        glue_client.start_crawler(Name=CRAWLER_NAME)
        print(f"Crawler run started successfully.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "CrawlerRunningException":
            print("Crawler is already running.")
        else:
            print(f"Error starting crawler: {e}")
            sys.exit(1)
            
    # 4. Poll Crawler run state until complete
    print("Waiting for crawler to complete execution...")
    while True:
        try:
            response = glue_client.get_crawler(Name=CRAWLER_NAME)
            crawler_state = response["Crawler"]["State"]
            crawler_metrics = response["Crawler"].get("LastCrawl", {})
            print(f"Current Crawler State: {crawler_state}")
            
            if crawler_state == "READY":
                status = crawler_metrics.get("Status")
                error_msg = crawler_metrics.get("ErrorMessage")
                print(f"Crawler completed. Crawl Status: {status}")
                if error_msg:
                    print(f"Crawler Error Message: {error_msg}")
                
                if status == "SUCCEEDED":
                    print("Updating table and partitions to Amazon Ion SerDe to support pretty-printed JSON...")
                    update_table_and_partitions_serde(glue_client)
                break
                
        except ClientError as e:
            print(f"Error fetching crawler status: {e}")
            
        time.sleep(15)
        
    print("Glue Deployment script completed successfully.")

def update_table_and_partitions_serde(glue_client) -> None:
    table_name = "source_remoteok"
    
    # 1. Update Table
    try:
        response = glue_client.get_table(DatabaseName=DATABASE_NAME, Name=table_name)
        table = response["Table"]
        
        table["StorageDescriptor"]["SerdeInfo"]["SerializationLibrary"] = "com.amazon.ionhiveserde.IonHiveSerDe"
        table["StorageDescriptor"]["InputFormat"] = "com.amazon.ionhiveserde.formats.IonInputFormat"
        table["StorageDescriptor"]["OutputFormat"] = "com.amazon.ionhiveserde.formats.IonOutputFormat"
        table["StorageDescriptor"]["SerdeInfo"]["Parameters"] = {}
        
        # Pop read-only fields
        for k in ["DatabaseName", "CreateTime", "UpdateTime", "CreatedBy", "IsRegisteredWithLakeFormation", "CatalogId", "VersionId", "FederatedTable", "IsMultiDialectView", "IsMaterializedView"]:
            table.pop(k, None)
            
        glue_client.update_table(DatabaseName=DATABASE_NAME, TableInput=table)
        print(f"Successfully updated table '{table_name}' to Amazon Ion SerDe.")
    except ClientError as e:
        print(f"Failed to update table SerDe: {e}")
        return

    # 2. Update Partitions
    try:
        paginator = glue_client.get_paginator("get_partitions")
        partitions = []
        for page in paginator.paginate(DatabaseName=DATABASE_NAME, TableName=table_name):
            partitions.extend(page["Partitions"])
            
        for partition in partitions:
            partition["StorageDescriptor"]["SerdeInfo"]["SerializationLibrary"] = "com.amazon.ionhiveserde.IonHiveSerDe"
            partition["StorageDescriptor"]["InputFormat"] = "com.amazon.ionhiveserde.formats.IonInputFormat"
            partition["StorageDescriptor"]["OutputFormat"] = "com.amazon.ionhiveserde.formats.IonOutputFormat"
            partition["StorageDescriptor"]["SerdeInfo"]["Parameters"] = {}
            
            p_val = partition["Values"]
            # Pop read-only fields
            for k in ["DatabaseName", "TableName", "CreationTime", "LastAccessTime", "CatalogId", "VersionId"]:
                partition.pop(k, None)
                
            glue_client.update_partition(
                DatabaseName=DATABASE_NAME,
                TableName=table_name,
                PartitionValueList=p_val,
                PartitionInput=partition
            )
        print(f"Successfully updated {len(partitions)} partitions to Amazon Ion SerDe.")
    except ClientError as e:
        print(f"Failed to update partitions SerDe: {e}")

if __name__ == "__main__":
    main()
