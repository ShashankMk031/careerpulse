"""
Configuration module for the CareerPulse ingestion pipeline.
Responsible for reading environment variables and defining pipeline constants.
No magic values or business logic allowed here.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ingestion Pipeline Metadata
PIPELINE_VERSION = "0.1.0"
SCHEMA_VERSION = 1

# Source Constants
SOURCE_NAME = "remoteok"
SOURCE_VERSION = "v1"
REMOTEOK_API_URL = "https://remoteok.com/api"

# HTTP API Request Configuration
REQUEST_TIMEOUT = 30  # seconds
API_MAX_RETRIES = 3
API_BACKOFF_FACTOR = 1.0  # seconds
API_STATUS_FORCELIST = [500, 502, 503, 504]

# AWS / S3 Configuration
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET = os.getenv("S3_BUCKET")

# S3 Uploader Retry Configuration
S3_MAX_RETRIES = 3
S3_BACKOFF_FACTOR = 1.5  # seconds
S3_TRANSIENT_ERRORS = [
    "SlowDown",
    "RequestLimitExceeded",
    "InternalError",
    "ServiceUnavailable",
    "Throttling",
]

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"