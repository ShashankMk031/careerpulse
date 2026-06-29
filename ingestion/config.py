from dotenv import load_dotenv 
import os 

load_dotenv() 

REMOTEOK_API_URL = "https://remoteok.com/api" 
REQUEST_TIMEOUT = 30 
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1") 
S3_BUCKET = os.getenv("S3_BUCKET")