"""
Orchestrates provisioning the Amazon RDS PostgreSQL database instance
and configuring the restricted security group for serving layer queries.
"""

import os
import sys
import time
import requests
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load workspace .env configuration
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
DB_IDENTIFIER = "cp-dev-serving-db"
DB_NAME = "serving_db"
DB_USER = "postgres"
# If DB_PASSWORD isn't configured, fall back to a secure default for dev
DB_PASSWORD = os.getenv("DB_PASSWORD", "cp_dev_postgres_password_123")
DB_CLASS = "db.t4g.micro"
DB_ENGINE = "postgres"
DB_ENGINE_VERSION = "16.13"
PORT = 5432
SG_NAME = "cp-dev-rds-sg"
VPC_ID = "vpc-099780d66b11446ab"

def get_developer_public_ip() -> str:
    """
    Fetches the current public IP of the developer machine dynamically.
    """
    try:
        response = requests.get("https://api.ipify.org", timeout=5)
        response.raise_for_status()
        ip = response.text.strip()
        print(f"Detected developer public IP: {ip}")
        return ip
    except Exception as e:
        print(f"Warning: Could not fetch public IP dynamically: {e}")
        return None

def setup_security_group(ec2_client, allowed_cidr: str) -> str:
    """
    Creates cp-dev-rds-sg if it does not exist, and updates ingress rules.
    """
    print(f"Checking for Security Group: {SG_NAME}...")
    sg_id = None
    try:
        response = ec2_client.describe_security_groups(
            Filters=[
                {"Name": "group-name", "Values": [SG_NAME]},
                {"Name": "vpc-id", "Values": [VPC_ID]}
            ]
        )
        sgs = response.get("SecurityGroups", [])
        if sgs:
            sg_id = sgs[0]["GroupId"]
            print(f"Found existing Security Group: {SG_NAME} ({sg_id})")
    except ClientError as e:
        print(f"Error checking security groups: {e}")
        
    if not sg_id:
        print(f"Creating new Security Group: {SG_NAME} inside VPC {VPC_ID}...")
        try:
            response = ec2_client.create_security_group(
                GroupName=SG_NAME,
                Description="CareerPulse Serving RDS Security Group with restricted ingress",
                VpcId=VPC_ID
            )
            sg_id = response["GroupId"]
            print(f"Created Security Group successfully: {sg_id}")
        except ClientError as e:
            print(f"Failed to create security group: {e}")
            sys.exit(1)
            
    # Authorize TCP Inbound Port 5432 for the CIDR
    print(f"Ensuring ingress rule allows TCP Port {PORT} from CIDR: {allowed_cidr}...")
    try:
        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": PORT,
                    "ToPort": PORT,
                    "IpRanges": [
                        {
                            "CidrIp": allowed_cidr,
                            "Description": "Serving database access from allowed CIDR"
                        }
                    ]
                }
            ]
        )
        print("Successfully added ingress rule.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidPermission.Duplicate":
            print("Ingress rule already exists. Skipping authorization.")
        else:
            print(f"Failed to authorize security group ingress: {e}")
            sys.exit(1)
            
    return sg_id

def provision_rds_instance(rds_client, sg_id: str):
    """
    Creates DB instance or waits for it if it is already provisioning.
    """
    print(f"Checking for RDS Database instance: {DB_IDENTIFIER}...")
    db_instance = None
    try:
        response = rds_client.describe_db_instances(DBInstanceIdentifier=DB_IDENTIFIER)
        db_instance = response["DBInstances"][0]
        print(f"Database instance {DB_IDENTIFIER} already exists.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "DBInstanceNotFound":
            print("Database instance not found. Initiating creation...")
        else:
            print(f"Error describing DB instance: {e}")
            sys.exit(1)
            
    if not db_instance:
        try:
            response = rds_client.create_db_instance(
                DBInstanceIdentifier=DB_IDENTIFIER,
                AllocatedStorage=20,
                DBInstanceClass=DB_CLASS,
                Engine=DB_ENGINE,
                EngineVersion=DB_ENGINE_VERSION,
                MasterUsername=DB_USER,
                MasterUserPassword=DB_PASSWORD,
                VpcSecurityGroupIds=[sg_id],
                PubliclyAccessible=True,
                DBName=DB_NAME,
                Tags=[{"Key": "Project", "Value": "CareerPulse"}]
            )
            db_instance = response["DBInstance"]
            print(f"RDS Database creation initiated. Identifier: {DB_IDENTIFIER}")
        except ClientError as e:
            print(f"Failed to create DB instance: {e}")
            sys.exit(1)
            
    status = db_instance.get("DBInstanceStatus", "")
    print(f"Current DB Instance Status: {status}")
    
    if status != "available":
        print("Waiting for database instance to enter 'available' state (this usually takes 3-7 minutes)...")
        try:
            waiter = rds_client.get_waiter("db_instance_available")
            waiter.wait(
                DBInstanceIdentifier=DB_IDENTIFIER,
                WaiterConfig={"Delay": 15, "MaxAttempts": 40}
            )
            print("Database instance is now available!")
            
            # Fetch updated description
            response = rds_client.describe_db_instances(DBInstanceIdentifier=DB_IDENTIFIER)
            db_instance = response["DBInstances"][0]
        except Exception as e:
            print(f"Error waiting for DB instance: {e}")
            sys.exit(1)
            
    endpoint_address = db_instance["Endpoint"]["Address"]
    print("\n" + "="*80)
    print("RDS PROVISIONING COMPLETE")
    print("="*80)
    print(f"DB Host (Endpoint): {endpoint_address}")
    print(f"DB Port:            {PORT}")
    print(f"DB Name:            {DB_NAME}")
    print(f"DB User:            {DB_USER}")
    print(f"DB Password:        {DB_PASSWORD}")
    print("="*80)
    print("\nACTION REQUIRED: Please update your local .env configuration with:")
    print(f"DB_HOST={endpoint_address}")
    print(f"DB_PORT={PORT}")
    print(f"DB_NAME={DB_NAME}")
    print(f"DB_USER={DB_USER}")
    print(f"DB_PASSWORD={DB_PASSWORD}")
    print("="*80)

def main():
    print("Initializing EC2 and RDS AWS Clients...")
    session = boto3.Session(region_name=AWS_REGION)
    ec2_client = session.client("ec2")
    rds_client = session.client("rds")
    
    # Resolve CIDR block: Use ALLOWED_CIDR env var, or dynamically detect public IP, or fall back to /32
    allowed_cidr = os.getenv("ALLOWED_CIDR")
    if not allowed_cidr:
        public_ip = get_developer_public_ip()
        if public_ip:
            allowed_cidr = f"{public_ip}/32"
        else:
            print("Error: Could not determine public IP and ALLOWED_CIDR env var is not set.")
            sys.exit(1)
            
    sg_id = setup_security_group(ec2_client, allowed_cidr)
    provision_rds_instance(rds_client, sg_id)

if __name__ == "__main__":
    main()
