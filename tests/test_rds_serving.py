"""
Unit and integration tests for the CareerPulse RDS Serving Layer.
Tests connection credentials, schema creation steps, dataset validation, type conversions,
transactional rollbacks, and psycopg bulk loaders.
"""

import unittest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime, timezone
import psycopg2

from backend.database.connection import get_db_credentials, get_connection
from backend.database.loader import (
    validate_dataset,
    transform_dataset_if_needed,
    upsert_dataset
)
from backend.database.metadata import log_load_metadata

class TestRDSServingLayer(unittest.TestCase):

    @patch.dict("os.environ", {
        "DB_ENVIRONMENT": "RDS",
        "DB_HOST": "mock-db-host",
        "DB_PORT": "5432",
        "DB_NAME": "mock_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "secure_password",
        "LOCAL_DB_HOST": "mock-local-host",
        "LOCAL_DB_PORT": "5433",
        "LOCAL_DB_NAME": "local_db",
        "LOCAL_DB_USER": "local_user",
        "LOCAL_DB_PASSWORD": "local_password"
    })
    def test_get_db_credentials_rds(self):
        """
        Verifies that RDS credentials are read when environment is RDS.
        """
        creds = get_db_credentials()
        self.assertEqual(creds["host"], "mock-db-host")
        self.assertEqual(creds["port"], "5432")
        self.assertEqual(creds["database"], "mock_db")
        self.assertEqual(creds["user"], "test_user")
        self.assertEqual(creds["password"], "secure_password")

    @patch.dict("os.environ", {
        "DB_ENVIRONMENT": "LOCAL",
        "DB_HOST": "mock-db-host",
        "DB_PORT": "5432",
        "DB_NAME": "mock_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "secure_password",
        "LOCAL_DB_HOST": "mock-local-host",
        "LOCAL_DB_PORT": "5433",
        "LOCAL_DB_NAME": "local_db",
        "LOCAL_DB_USER": "local_user",
        "LOCAL_DB_PASSWORD": "local_password"
    })
    def test_get_db_credentials_local(self):
        """
        Verifies that LOCAL credentials are read when environment is LOCAL.
        """
        creds = get_db_credentials()
        self.assertEqual(creds["host"], "mock-local-host")
        self.assertEqual(creds["port"], "5433")
        self.assertEqual(creds["database"], "local_db")
        self.assertEqual(creds["user"], "local_user")
        self.assertEqual(creds["password"], "local_password")

    def test_validate_company_dataset(self):
        """
        Verifies that validation correctly detects primary key omissions and constraint violations.
        """
        records = [
            {"company": "Google", "total_jobs": 10},
            {"company": "", "total_jobs": 5},          # Missing PK
            {"company": "Amazon", "total_jobs": -1}     # Constraint violation: negative jobs
        ]
        
        valid, invalid = validate_dataset(records, "company")
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(invalid), 2)
        self.assertEqual(valid[0]["company"], "Google")
        self.assertIn("Missing required primary key", invalid[0]["__error__"])
        self.assertIn("Constraint violation", invalid[1]["__error__"])

    def test_validate_summary_dataset(self):
        """
        Verifies remote percentage constraint pre-validation for summary metrics.
        """
        records = [
            {"remote_percentage": 50.0},
            {"remote_percentage": 105.0} # Out of range: > 100
        ]
        valid, invalid = validate_dataset(records, "summary")
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(invalid), 1)
        self.assertIn("Constraint violation", invalid[0]["__error__"])

    def test_transform_dataset_if_needed(self):
        """
        Verifies that strings are trimmed and tags are standardized to lowercase.
        """
        records = [
            {"company": "  Microsoft  ", "position": "Developer"},
            {"tag": "  PYTHON  "}
        ]
        
        res1 = transform_dataset_if_needed([records[0]], "company")
        res2 = transform_dataset_if_needed([records[1]], "skills")
        
        self.assertEqual(res1[0]["company"], "Microsoft")
        self.assertEqual(res2[0]["tag"], "python")

    @patch("backend.database.pool._connection_pool")
    def test_connection_transaction_commit_on_success(self, mock_pool):
        """
        Verifies that connections are committed on successful completion.
        """
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn
        
        with patch.dict("os.environ", {"DB_HOST": "mock-host"}):
            with get_connection() as conn:
                self.assertEqual(conn, mock_conn)
                
        mock_conn.commit.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)
        mock_conn.rollback.assert_not_called()

    @patch("backend.database.pool._connection_pool")
    def test_connection_rollback_on_failure(self, mock_pool):
        """
        Verifies that rollback is called if exceptions occur within the context.
        """
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn
        
        with patch.dict("os.environ", {"DB_HOST": "mock-host"}):
            with self.assertRaises(ValueError):
                with get_connection() as conn:
                    raise ValueError("Triggered failure")
                    
        mock_conn.rollback.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)
        mock_conn.commit.assert_not_called()

    @patch("psycopg2.extras.execute_values")
    def test_upsert_company_dataset(self, mock_execute_values):
        """
        Verifies that bulk upsert uses ON CONFLICT DO UPDATE and returns xmax counts.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock execute_values return value for fetch=True
        mock_execute_values.return_value = [(True,), (True,), (False,)]
        
        records = [
            {"company": "Google", "total_jobs": 10, "unique_locations": 1, "avg_salary_min": 100.0, "avg_salary_max": 200.0, "original_jobs_count": 5, "highest_paying_role": "SWE", "latest_posting": None, "jobs_with_salary": 2},
            {"company": "Apple", "total_jobs": 5, "unique_locations": 1, "avg_salary_min": 150.0, "avg_salary_max": 250.0, "original_jobs_count": 2, "highest_paying_role": "Architect", "latest_posting": None, "jobs_with_salary": 1},
            {"company": "Netflix", "total_jobs": 3, "unique_locations": 1, "avg_salary_min": 120.0, "avg_salary_max": 220.0, "original_jobs_count": 1, "highest_paying_role": "Manager", "latest_posting": None, "jobs_with_salary": 1}
        ]
        
        ins, upd = upsert_dataset(mock_conn, records, "company")
        
        mock_execute_values.assert_called_once()
        query = mock_execute_values.call_args[0][1]
        self.assertIn("ON CONFLICT (company)", query)
        self.assertIn("DO UPDATE SET", query)
        
        self.assertEqual(ins, 2)
        self.assertEqual(upd, 1)

    @patch("psycopg2.extras.execute_values")
    def test_replace_summary_dataset(self, mock_execute_values):
        """
        Verifies that summary table uses REPLACE refresh strategy (truncate then insert).
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        records = [{
            "total_jobs": 100, "total_companies": 85, "total_locations": 80, "remote_jobs": 50,
            "remote_percentage": 50.0, "average_salary": 120000.0, "median_salary": 110000.0, "highest_salary": 200000.0,
            "highest_paying_company": "Netflix", "top_company": "Google", "top_skill": "python", "top_country": "USA",
            "jobs_with_salary": 90, "jobs_without_salary": 10, "generation_timestamp": datetime.now()
        }]
        
        ins, upd = upsert_dataset(mock_conn, records, "summary")
        
        # Verify truncate executed
        mock_cursor.execute.assert_called_once_with("TRUNCATE TABLE serving.hiring_summary;")
        mock_execute_values.assert_called_once()
        
        self.assertEqual(ins, 1)
        self.assertEqual(upd, 0)

    def test_log_load_metadata(self):
        """
        Verifies that load logs are formatted and written correctly to metadata fields.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        meta = {
            "pipeline_execution_id": "test_exec_id",
            "source_pipeline_execution_id": "source_id",
            "table_name": "serving.company_analytics",
            "dataset_name": "company",
            "load_type": "UPSERT",
            "status": "SUCCESS",
            "records_loaded": 10,
            "records_failed": 0,
            "rows_inserted": 8,
            "rows_updated": 2,
            "load_duration_ms": 150,
            "error_message": None,
            "start_time": datetime.now(),
            "end_time": datetime.now(),
            "generation_timestamp": datetime.now()
        }
        
        log_load_metadata(mock_conn, meta)
        mock_cursor.execute.assert_called_once()
        
        # Assert placeholders query list matches
        sql_query = mock_cursor.execute.call_args[0][0]
        self.assertIn("INSERT INTO serving.load_metadata", sql_query)

    @patch("backend.database.pool.get_pool_config")
    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_threaded_connection_pooling(self, mock_pool_class, mock_get_config):
        """
        Verifies initialization and release interfaces for our connection pool.
        """
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_get_config.return_value = {
            "host": "mock-host",
            "port": "5432",
            "database": "mock_db",
            "user": "test_user",
            "password": "secure_password",
            "minconn": 2,
            "maxconn": 10,
        }
        
        import backend.database.pool
        backend.database.pool._connection_pool = None
        
        backend.database.pool.initialize_pool()
        backend.database.pool.close_pool()
            
        mock_pool_class.assert_called_once_with(
            minconn=2,
            maxconn=10,
            host="mock-host",
            port="5432",
            database="mock_db",
            user="test_user",
            password="secure_password"
        )
        mock_pool.closeall.assert_called_once()

    def test_view_queries_present_in_schema(self):
        """
        Verifies database view DDL statements are declared.
        """
        from backend.database.schema import CREATE_VIEW_QUERIES
        self.assertEqual(len(CREATE_VIEW_QUERIES), 5)
        self.assertIn("v_top_companies", CREATE_VIEW_QUERIES[0])
        self.assertIn("v_top_skills", CREATE_VIEW_QUERIES[1])
        self.assertIn("v_top_countries", CREATE_VIEW_QUERIES[2])
        self.assertIn("v_dashboard_summary", CREATE_VIEW_QUERIES[3])
        self.assertIn("v_dataset_status", CREATE_VIEW_QUERIES[4])

if __name__ == "__main__":
    unittest.main()
