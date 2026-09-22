import unittest
from unittest.mock import patch, MagicMock

# Start database pool patches globally to avoid network checks during lifespan setup
pool_init_patcher = patch("backend.database.pool.initialize_pool")
pool_close_patcher = patch("backend.database.pool.close_pool")
mock_pool_init = pool_init_patcher.start()
mock_pool_close = pool_close_patcher.start()

from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import get_db

# Mock DB connection and override get_db dependency globally
mock_db_conn = MagicMock()
mock_cursor = MagicMock()
mock_db_conn.cursor.return_value.__enter__.return_value = mock_cursor

def override_get_db():
    yield mock_db_conn

app.dependency_overrides[get_db] = override_get_db

from backend.app.models.entities import (
    HiringSummary, DatasetFreshness, CompanyAnalytics, 
    SkillAnalytics, TechnologyAnalytics, GeographyAnalytics, SalaryAnalytics
)
from backend.app.exceptions import NotFoundException, ValidationException, DatabaseException

client = TestClient(app, raise_server_exceptions=False)

class TestServingAPI(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        pool_init_patcher.stop()
        pool_close_patcher.stop()

    def test_root_endpoint(self):
        """
        Verifies GET / returns standard status details.
        """
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["title"], "CareerPulse Serving API")
        self.assertEqual(json_data["data"]["status"], "online")

    def test_version_endpoint(self):
        """
        Verifies GET /version returns system version and git hash info.
        """
        response = client.get("/version")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertIn("version", json_data["data"])
        self.assertIn("git_commit", json_data["data"])
        self.assertIn("build_timestamp", json_data["data"])
        self.assertIn("python_version", json_data["data"])

    def test_health_endpoint_success(self):
        """
        Verifies GET /health returns DB connection success statuses.
        """
        mock_cursor.execute.reset_mock()

        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["database"], "connected")
        mock_cursor.execute.assert_called_once_with("SELECT 1;")

    @patch("backend.app.main.get_db")
    @patch("backend.app.main.SummaryService.get_dataset_freshness")
    def test_metrics_endpoint(self, mock_get_freshness, mock_get_db):
        """
        Verifies GET /metrics lists dataset lag stats correctly.
        """
        mock_get_db.return_value = [MagicMock()]
        mock_get_freshness.return_value = [
            DatasetFreshness(
                dataset="company",
                last_refresh=datetime.now(timezone.utc),
                current_age="00:05:00",
                source_generation_timestamp=datetime.now(timezone.utc),
                refresh_lag_minutes=15.0,
                status="FRESH"
            )
        ]

        response = client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(len(json_data["data"]), 1)
        self.assertEqual(json_data["data"][0]["dataset"], "company")
        self.assertEqual(json_data["data"][0]["status"], "FRESH")

    @patch("backend.app.routers.summary.get_db")
    @patch("backend.app.routers.summary.SummaryService.get_dashboard_summary")
    def test_summary_endpoint(self, mock_get_summary, mock_get_db):
        """
        Verifies GET /summary exposes KPIs from hiring summary.
        """
        mock_get_db.return_value = [MagicMock()]
        mock_get_summary.return_value = HiringSummary(
            id=1, total_jobs=100, total_companies=10, total_locations=5,
            remote_jobs=40, remote_percentage=40.0, average_salary=120000.0,
            median_salary=110000.0, highest_salary=200000.0,
            highest_paying_company="Google", top_company="Amazon",
            top_skill="Python", top_country="USA", jobs_with_salary=50,
            jobs_without_salary=50, generation_timestamp=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
        )

        response = client.get("/api/v1/summary")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "public, max-age=300")
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["total_jobs"], 100)
        self.assertEqual(json_data["data"]["top_skill"], "Python")

    @patch("backend.app.routers.companies.get_db")
    @patch("backend.app.routers.companies.CompaniesService.get_companies")
    def test_companies_list_pagination(self, mock_get_companies, mock_get_db):
        """
        Verifies pagination calculations and schema format wrapping.
        """
        mock_get_db.return_value = [MagicMock()]
        mock_get_companies.return_value = ([
            CompanyAnalytics(
                company="Google", total_jobs=10, unique_locations=2,
                avg_salary_min=100000.0, avg_salary_max=150000.0,
                original_jobs_count=12, highest_paying_role="Staff Eng",
                latest_posting=datetime.now(timezone.utc), jobs_with_salary=8,
                created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
            )
        ], 25)

        response = client.get("/api/v1/companies?page=2&page_size=10")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(len(json_data["data"]), 1)
        self.assertEqual(json_data["metadata"]["page"], 2)
        self.assertEqual(json_data["metadata"]["total_pages"], 3)
        self.assertTrue(json_data["metadata"]["has_next"])
        self.assertTrue(json_data["metadata"]["has_previous"])

    def test_companies_validation_errors(self):
        """
        Verifies validation boundaries for page and page_size parameters.
        """
        # Page size too large
        response = client.get("/api/v1/companies?page=1&page_size=101")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        self.assertIn("VALIDATION_ERROR", response.json()["error_code"])

        # Page index less than 1
        response = client.get("/api/v1/companies?page=0&page_size=20")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    @patch("backend.app.routers.companies.get_db")
    @patch("backend.app.routers.companies.CompaniesService.get_company_by_name")
    def test_company_details_success(self, mock_get_company, mock_get_db):
        """
        Verifies single company lookup detail return.
        """
        mock_get_db.return_value = [MagicMock()]
        mock_get_company.return_value = CompanyAnalytics(
            company="Google", total_jobs=10, unique_locations=2,
            avg_salary_min=100000.0, avg_salary_max=150000.0,
            original_jobs_count=12, highest_paying_role="Staff Eng",
            latest_posting=datetime.now(timezone.utc), jobs_with_salary=8,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
        )

        response = client.get("/api/v1/companies/Google")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["company"], "Google")

    @patch("backend.app.routers.companies.get_db")
    @patch("backend.app.routers.companies.CompaniesService.get_company_by_name")
    def test_company_details_not_found(self, mock_get_company, mock_get_db):
        """
        Verifies 404 error envelope when single company is missing.
        """
        mock_get_db.return_value = [MagicMock()]
        mock_get_company.side_effect = NotFoundException("Company 'Unknown' not found.")

        response = client.get("/api/v1/companies/Unknown")
        self.assertEqual(response.status_code, 404)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["error_code"], "RESOURCE_NOT_FOUND")

    @patch("backend.app.routers.skills.get_db")
    @patch("backend.app.routers.skills.SkillsService.get_skills")
    def test_skills_paginated_list(self, mock_get_skills, mock_get_db):
        """
        Verifies skills listing endpoint.
        """
        mock_get_db.return_value = [MagicMock()]
        mock_get_skills.return_value = ([
            SkillAnalytics(
                tag="python", job_demand_count=50, avg_salary_min=90000.0,
                avg_salary_max=130000.0, salary_premium=10000.0,
                remote_jobs_count=25, created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        ], 1)

        response = client.get("/api/v1/skills")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "public, max-age=3600")
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"][0]["tag"], "python")

    @patch("backend.app.routers.technology.get_db")
    @patch("backend.app.routers.technology.TechnologyService.get_technology_analytics")
    def test_technology_paginated_list(self, mock_get_tech, mock_get_db):
        """
        Verifies technology analytics endpoint.
        """
        mock_get_db.return_value = [MagicMock()]
        mock_get_tech.return_value = ([
            TechnologyAnalytics(
                tech_tag="fastapi", job_demand_count=15, avg_salary_min=100000.0,
                avg_salary_max=140000.0, top_company="Netflix",
                created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
            )
        ], 1)

        response = client.get("/api/v1/technology")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "public, max-age=3600")
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"][0]["tech_tag"], "fastapi")

    @patch("backend.app.routers.geography.get_db")
    @patch("backend.app.routers.geography.GeographyService.get_geography_stats")
    def test_geography_endpoints(self, mock_get_geo, mock_get_db):
        """
        Verifies geographical aggregation checks.
        """
        mock_get_db.return_value = [MagicMock()]
        mock_get_geo.return_value = [
            GeographyAnalytics(
                country="India", region="Bangalore", jobs_count=30,
                avg_salary_min=15000.0, avg_salary_max=35000.0,
                company_count=5, remote_count=5, onsite_count=20, hybrid_count=5,
                created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
            )
        ]

        response = client.get("/api/v1/geography?country=India")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"][0]["region"], "Bangalore")

    @patch("backend.app.routers.salary.get_db")
    @patch("backend.app.routers.salary.SalaryService.get_salary_tiers")
    def test_salary_tiers_list(self, mock_get_salary, mock_get_db):
        """
        Verifies salary bracket analytics endpoint.
        """
        mock_get_db.return_value = [MagicMock()]
        mock_get_salary.return_value = [
            SalaryAnalytics(
                salary_tier="$100k-$120k", jobs_count=45,
                avg_salary_min=100000.0, avg_salary_max=120000.0,
                created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
            )
        ]

        response = client.get("/api/v1/salary")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"][0]["salary_tier"], "$100k-$120k")

    @patch("backend.app.routers.summary.get_db")
    @patch("backend.app.routers.summary.SummaryService.get_dashboard_summary")
    def test_server_error_mapping(self, mock_get_summary, mock_get_db):
        """
        Verifies unhandled generic errors return a standard 500 error envelope.
        """
        mock_get_db.return_value = [MagicMock()]
        mock_get_summary.side_effect = Exception("System crash")

        response = client.get("/api/v1/summary")
        self.assertEqual(response.status_code, 500)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["error_code"], "UNHANDLED_SERVER_ERROR")
        self.assertEqual(json_data["error"], "An unexpected server error occurred.")

    @patch("backend.app.routers.skills.get_db")
    @patch("backend.app.routers.skills.SkillsService.get_skills")
    def test_gzip_compression(self, mock_get_skills, mock_get_db):
        """
        Verifies GZip middleware compresses payloads larger than 1024 bytes.
        """
        mock_get_db.return_value = [MagicMock()]
        skills_list = [
            SkillAnalytics(
                tag=f"skill_{i}", job_demand_count=i, avg_salary_min=100000.0,
                avg_salary_max=150000.0, salary_premium=10000.0,
                remote_jobs_count=i, created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            for i in range(50)
        ]
        mock_get_skills.return_value = (skills_list, 50)

        response = client.get("/api/v1/skills", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Encoding"), "gzip")

from concurrent.futures import ThreadPoolExecutor
from io import StringIO
import sys
import json
from backend.app.utils.context import (
    DBTimingAccumulator,
    db_timing_ctx,
    get_db_duration,
    reset_db_timing,
    track_db_time,
    db_duration_ctx,
    get_or_create_db_timing
)
from backend.app.repositories.summary import SummaryRepository

class TestDatabaseTimingInstrumentation(unittest.TestCase):
    """
    Focused test suite proving:
    a. Decorated repository calls produce non-zero accumulated DB timing;
    b. RequestLoggingMiddleware exposes the accumulated value in X-Database-Time-MS;
    c. Concurrent/request-scoped calls do not leak timing across requests;
    d. api_duration remains non-negative and correctly computed;
    e. get_db() initializes/resets timing exactly once per request.
    """

    def setUp(self):
        # Reset mock cursor
        mock_cursor.reset_mock()

    def test_decorated_repository_call_produces_nonzero_timing(self):
        """
        Requirement 3a: Proves a decorated repository method accumulates non-zero DB timing.
        """
        mock_cursor.fetchone.return_value = (
            1, 100, 10, 5, 40, 40.0, 120000.0, 110000.0, 200000.0,
            "Google", "Amazon", "Python", "USA", 50, 50,
            datetime.now(timezone.utc), datetime.now(timezone.utc), datetime.now(timezone.utc)
        )
        reset_db_timing()
        self.assertEqual(get_db_duration(), 0.0)

        # Call decorated repository method
        result = SummaryRepository.get_kpis(mock_db_conn)
        self.assertIsNotNone(result)
        
        timing_val = get_db_duration()
        self.assertGreater(timing_val, 0.0)
        
        acc = db_timing_ctx.get()
        self.assertIsNotNone(acc)
        self.assertEqual(acc.call_count, 1)

        # Call second decorated method to verify accumulation
        mock_cursor.fetchall.return_value = []
        SummaryRepository.get_freshness_metrics(mock_db_conn)
        self.assertGreater(get_db_duration(), timing_val)
        self.assertEqual(acc.call_count, 2)

    def test_middleware_exposes_accumulated_db_time_header(self):
        """
        Requirement 3b: Proves RequestLoggingMiddleware exposes accumulated DB time in X-Database-Time-MS.
        """
        mock_cursor.fetchone.return_value = (
            1, 100, 10, 5, 40, 40.0, 120000.0, 110000.0, 200000.0,
            "Google", "Amazon", "Python", "USA", 50, 50,
            datetime.now(timezone.utc), datetime.now(timezone.utc), datetime.now(timezone.utc)
        )

        response = client.get("/api/v1/summary")
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Request-ID", response.headers)
        self.assertIn("X-Process-Time-MS", response.headers)
        self.assertIn("X-Database-Time-MS", response.headers)

        db_time = float(response.headers["X-Database-Time-MS"])
        process_time = float(response.headers["X-Process-Time-MS"])
        self.assertGreater(db_time, 0.0)
        self.assertGreaterEqual(process_time, 0.0)

        # Endpoint without DB queries returns 0.00
        res_no_db = client.get("/")
        self.assertEqual(res_no_db.status_code, 200)
        self.assertEqual(res_no_db.headers.get("X-Database-Time-MS"), "0.00")

    def test_concurrent_request_isolation(self):
        """
        Requirement 3c: Proves concurrent/request-scoped calls do not leak timing into another request.
        """
        mock_cursor.fetchone.return_value = (
            1, 100, 10, 5, 40, 40.0, 120000.0, 110000.0, 200000.0,
            "Google", "Amazon", "Python", "USA", 50, 50,
            datetime.now(timezone.utc), datetime.now(timezone.utc), datetime.now(timezone.utc)
        )

        def make_db_request():
            res = client.get("/api/v1/summary")
            return "db", float(res.headers.get("X-Database-Time-MS", "0.00"))

        def make_no_db_request():
            res = client.get("/")
            return "no_db", float(res.headers.get("X-Database-Time-MS", "0.00"))

        tasks = []
        for _ in range(15):
            tasks.append(make_db_request)
            tasks.append(make_no_db_request)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fn) for fn in tasks]
            results = [f.result() for f in futures]

        for req_type, db_ms in results:
            if req_type == "no_db":
                self.assertEqual(db_ms, 0.0, "Non-DB request was contaminated by concurrent DB request!")
            elif req_type == "db":
                self.assertGreater(db_ms, 0.0, "DB request failed to record timing!")

    def test_api_duration_calculation_and_non_negative(self):
        """
        Requirement 3d: Proves api_duration remains non-negative: max(0.0, total - db).
        """
        # Test mathematical edge cases
        self.assertEqual(max(0.0, 10.0 - 5.0), 5.0)
        self.assertEqual(max(0.0, 5.0 - 5.0), 0.0)
        self.assertEqual(max(0.0, 3.0 - 5.0), 0.0)

        # Test log output from actual request
        mock_cursor.fetchone.return_value = (
            1, 100, 10, 5, 40, 40.0, 120000.0, 110000.0, 200000.0,
            "Google", "Amazon", "Python", "USA", 50, 50,
            datetime.now(timezone.utc), datetime.now(timezone.utc), datetime.now(timezone.utc)
        )
        stdout_capture = StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = stdout_capture
            response = client.get("/api/v1/summary")
            self.assertEqual(response.status_code, 200)
        finally:
            sys.stdout = old_stdout

        log_lines = stdout_capture.getvalue().strip().split("\n")
        summary_log = None
        for line in log_lines:
            try:
                parsed = json.loads(line)
                if parsed.get("path") == "/api/v1/summary":
                    summary_log = parsed
                    break
            except Exception:
                continue

        self.assertIsNotNone(summary_log, "Structured JSON log for /api/v1/summary was not found")
        self.assertGreaterEqual(summary_log["api_duration"], 0.0)
        self.assertGreater(summary_log["database_duration"], 0.0)
        self.assertEqual(
            summary_log["api_duration"],
            round(max(0.0, summary_log["duration"] - summary_log["database_duration"]), 2)
        )

    def test_get_db_initializes_once_per_request(self):
        """
        Requirement 11: Proves get_db() initializes/resets timing exactly once per request.
        """
        # Patch pool so get_db can run its actual code
        with patch("backend.app.database.get_pooled_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_db_conn
            
            # 1. Start simulated request with fresh uninitialized accumulator
            acc = DBTimingAccumulator()
            token = db_timing_ctx.set(acc)
            try:
                self.assertFalse(acc.initialized)
                
                # First call to get_db in request
                db_gen = get_db()
                conn1 = next(db_gen)
                self.assertTrue(acc.initialized)
                self.assertEqual(acc.duration_ms, 0.0)

                # Simulate a query accumulating 15ms
                acc.add(15.0)
                self.assertEqual(acc.duration_ms, 15.0)

                # Second call to get_db in the same request must NOT reset timing
                db_gen2 = get_db()
                conn2 = next(db_gen2)
                self.assertTrue(acc.initialized)
                self.assertEqual(acc.duration_ms, 15.0)

                # Clean up generators
                try:
                    next(db_gen)
                except StopIteration:
                    pass
                try:
                    next(db_gen2)
                except StopIteration:
                    pass
            finally:
                db_timing_ctx.reset(token)

def tearDownModule():
    pool_init_patcher.stop()
    pool_close_patcher.stop()

if __name__ == "__main__":
    unittest.main()
