# Responsibity : 
# Call API -> Validate response -> Return python object -> Never touch S3 

import requests 
from config import REMOTEOK_API_URL, REQUEST_TIMEOUT

def fetch_jobs():
    response = requests.get(
        REMOTEOK_API_URL,
        headers = {"User-Agent": "CareerPulse"},
        timeout = REQUEST_TIMEOUT,
    )

    response.raise_for_status()  # Raise an exception and easier to debug 
    data = response.json()  # Parse the JSON response into a Python object 
    return data 
