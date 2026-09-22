"""
Database connection manager providing reusable psycopg2 connections.
Supports standard context manager operations to ensure clean resource releases.
"""

import os
from contextlib import contextmanager
import psycopg2
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

def get_db_credentials() -> dict:
    """
    Retrieves database connection credentials from environment variables.
    Supports switching between LOCAL and RDS database environments via DB_ENVIRONMENT.
    Supports standard 12-factor variables (DATABASE_*) with backwards-compatible fallbacks (DB_*).
    """
    db_env = os.getenv("DB_ENVIRONMENT", "RDS").strip().upper()
    schema = os.getenv("DATABASE_SCHEMA", "serving")
    
    if db_env == "LOCAL":
        return {
            "host": os.getenv("LOCAL_DB_HOST") or os.getenv("DATABASE_HOST", "localhost"),
            "port": os.getenv("LOCAL_DB_PORT") or os.getenv("DATABASE_PORT", "5433"),
            "database": os.getenv("LOCAL_DB_NAME") or os.getenv("DATABASE_NAME", "serving_db"),
            "user": os.getenv("LOCAL_DB_USER") or os.getenv("DATABASE_USER", "postgres"),
            "password": os.getenv("LOCAL_DB_PASSWORD") or os.getenv("DATABASE_PASSWORD") or os.getenv("DB_PASSWORD", ""),
            "schema": schema,
        }
    else:
        # Default environment: RDS (ensures zero changes to production behavior)
        return {
            "host": os.getenv("DB_HOST") or os.getenv("DATABASE_HOST"),
            "port": os.getenv("DB_PORT") or os.getenv("DATABASE_PORT", "5432"),
            "database": os.getenv("DB_NAME") or os.getenv("DATABASE_NAME", "serving_db"),
            "user": os.getenv("DB_USER") or os.getenv("DATABASE_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD") or os.getenv("DATABASE_PASSWORD", ""),
            "schema": schema,
        }

from backend.database.pool import get_pooled_connection, close_pool

@contextmanager
def get_connection():
    """
    Context manager yielding a pooled database connection from ThreadedConnectionPool.
    Kept for compatibility with existing modules.
    """
    with get_pooled_connection() as conn:
        yield conn
