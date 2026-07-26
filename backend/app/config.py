import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

class Settings:
    API_DEBUG: bool = os.getenv("API_DEBUG", "false").lower() in ("true", "1", "yes")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # CORS setup: comma-separated list of origins, e.g. "http://localhost:3000,http://localhost:8000"
    CORS_ORIGINS: list[str] = [
        origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()
    ]
    
    # Cache duration variables (seconds)
    CACHE_MAX_AGE_SUMMARY: int = int(os.getenv("CACHE_MAX_AGE_SUMMARY", "300"))
    CACHE_MAX_AGE_ANALYTICS: int = int(os.getenv("CACHE_MAX_AGE_ANALYTICS", "3600"))

    def __init__(self):
        # Validate critical database configuration settings at import-time to fail-fast
        db_env = os.getenv("DB_ENVIRONMENT", "RDS").strip().upper()
        if db_env == "LOCAL":
            # For local environment, check if port or user is missing (though we supply standard defaults)
            pass
        else:
            db_host = os.getenv("DB_HOST")
            if not db_host or not db_host.strip():
                raise ValueError(
                    "CRITICAL: Serving database host config 'DB_HOST' is missing or blank. "
                    "Please configure live S3-to-RDS credentials inside environment."
                )

settings = Settings()
