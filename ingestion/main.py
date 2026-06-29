# Responsibility : 
# Call RemoteOK -> Recieve data -> Call uploader -> Log success 

from remoteok import fetch_jobs
from logger import logger

def main(): 
    jobs = fetch_jobs() 
    logger.info(f"Fetched {len(jobs)} records")

if __name__ == "__main__": 
    main() 