"""
Automated serving layer health check script for CareerPulse Amazon RDS database.
Verifies connection status, latency, schemas, tables, index registrations, and disk sizing.
Returns exit code 0 on PASS, 1 on FAIL.
"""

import os
import sys
import time
import json

# Ensure backend package is discoverable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.connection import get_connection

REQUIRED_TABLES = [
    "company_analytics",
    "skills_analytics",
    "geography_analytics",
    "salary_analytics",
    "technology_analytics",
    "hiring_summary",
    "load_metadata"
]

REQUIRED_INDEXES = [
    "idx_company_total_jobs",
    "idx_skills_demand",
    "idx_tech_demand",
    "idx_geo_jobs_count"
]

def run_health_check() -> dict:
    report = {
        "status": "PASS",
        "connection_latency_ms": 0.0,
        "schema_ok": False,
        "tables_check": {},
        "indexes_check": {},
        "db_size_bytes": 0,
        "errors": []
    }
    
    start_time = time.perf_counter()
    try:
        # 1. Connectivity Check & Latency Measurement
        with get_connection() as conn:
            report["connection_latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
            
            with conn.cursor() as cursor:
                # 2. Schema existence check
                cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'serving';")
                schema_row = cursor.fetchone()
                if schema_row:
                    report["schema_ok"] = True
                else:
                    report["status"] = "FAIL"
                    report["errors"].append("Schema 'serving' does not exist in the database.")
                    
                # 3. Table existence checks
                for t in REQUIRED_TABLES:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'serving' AND table_name = %s
                        );
                    """, (t,))
                    exists = cursor.fetchone()[0]
                    report["tables_check"][t] = exists
                    if not exists:
                        report["status"] = "FAIL"
                        report["errors"].append(f"Table 'serving.{t}' is missing.")
                        
                # 4. Index existence checks
                for idx in REQUIRED_INDEXES:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM pg_class c
                            JOIN pg_namespace n ON n.oid = c.relnamespace
                            WHERE c.relname = %s AND n.nspname = 'serving' AND c.relkind = 'i'
                        );
                    """, (idx,))
                    exists = cursor.fetchone()[0]
                    report["indexes_check"][idx] = exists
                    if not exists:
                        report["status"] = "FAIL"
                        report["errors"].append(f"Index 'serving.{idx}' is missing.")
                        
                # 5. Database size check
                cursor.execute("SELECT pg_database_size(current_database());")
                report["db_size_bytes"] = cursor.fetchone()[0]
                
    except Exception as e:
        report["status"] = "FAIL"
        report["errors"].append(f"Database connection failed: {e}")
        
    return report

def main():
    report = run_health_check()
    print(json.dumps(report, indent=2))
    
    if report["status"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
