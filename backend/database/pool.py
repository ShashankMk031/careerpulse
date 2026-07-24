"""
Thread-safe PostgreSQL connection pooling module using psycopg2.pool.ThreadedConnectionPool.
Optimizes API query latency by reusing active database connection processes.
"""

import os
from contextlib import contextmanager
import psycopg2.pool
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Global connection pool instance
_connection_pool = None

from backend.database.connection import get_db_credentials

def get_pool_config() -> dict:
    """
    Retrieves database credentials and pool sizing bounds from environment variables.
    """
    creds = get_db_credentials()
    creds["minconn"] = int(os.getenv("DB_MIN_CONN", "2"))
    creds["maxconn"] = int(os.getenv("DB_MAX_CONN", "10"))
    return creds

def initialize_pool():
    """
    Initializes the global ThreadedConnectionPool if it doesn't already exist.
    ThreadedConnectionPool is thread-safe, making it suitable for future multi-threaded FastAPI servers.
    """
    global _connection_pool
    if _connection_pool is not None:
        return
        
    config = get_pool_config()
    if not config["host"]:
        raise ValueError("DB_HOST environment variable is not configured.")
        
    print(f"Initializing database connection pool (minconn={config['minconn']}, maxconn={config['maxconn']}) to host: {config['host']}...")
    try:
        _connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=config["minconn"],
            maxconn=config["maxconn"],
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=config["password"]
        )
        print("Database connection pool initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize database connection pool: {e}")
        raise e

def close_pool():
    """
    Closes all active database connections in the pool.
    Called during application shutdown sequence.
    """
    global _connection_pool
    if _connection_pool is None:
        return
        
    print("Closing all database connection pool streams...")
    try:
        _connection_pool.closeall()
        _connection_pool = None
        print("Database connection pool closed successfully.")
    except Exception as e:
        print(f"Error while closing database connection pool: {e}")

@contextmanager
def get_pooled_connection():
    """
    Context manager that yields a database connection from the ThreadedConnectionPool.
    Automatically commits transactions, handles rollbacks on failure, and releases
    the connection back to the pool.
    """
    global _connection_pool
    if _connection_pool is None:
        initialize_pool()
        
    conn = None
    try:
        conn = _connection_pool.getconn()
        yield conn
        # Commit transaction on successful block exit
        conn.commit()
    except Exception as e:
        if conn:
            print(f"Database transaction error occurred, executing rollback: {e}")
            try:
                conn.rollback()
            except Exception as rollback_err:
                print(f"Failed to execute database rollback: {rollback_err}")
        raise e
    finally:
        if conn and _connection_pool:
            try:
                _connection_pool.putconn(conn)
            except Exception as put_err:
                print(f"Failed to return connection back to pool: {put_err}")
