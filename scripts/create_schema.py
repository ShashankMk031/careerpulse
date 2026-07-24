"""
Orchestrates creating the database schema, normalized tables, CHECK constraints, and indexes
on the Amazon RDS PostgreSQL serving instance.
"""

import os
import sys

# Ensure backend package is discoverable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.connection import get_connection
from backend.database.schema import CREATE_SCHEMA_QUERY, CREATE_TABLES_QUERIES, CREATE_INDEX_QUERIES, CREATE_VIEW_QUERIES

def init_database_schema():
    print("Connecting to the Amazon RDS PostgreSQL Serving database...")
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Create serving schema
                print("Creating database schema...")
                cursor.execute(CREATE_SCHEMA_QUERY)
                print("Schema 'serving' created or verified successfully.")
                
                # 2. Create normalized tables
                print("Creating tables with CHECK constraints...")
                for query in CREATE_TABLES_QUERIES:
                    cursor.execute(query)
                print("Tables created successfully.")
                
                # 3. Create indexes
                print("Creating optimization indexes...")
                for query in CREATE_INDEX_QUERIES:
                    cursor.execute(query)
                print("Indexes created successfully.")
                
                # 4. Create views
                print("Creating database views for API consumption...")
                for query in CREATE_VIEW_QUERIES:
                    cursor.execute(query)
                print("Views created successfully.")
                
            print("\nDatabase Schema Initialization Complete!")
    except Exception as e:
        print(f"Error initializing serving database schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database_schema()
