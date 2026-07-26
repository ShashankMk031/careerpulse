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

def tearDownModule():
    pool_init_patcher.stop()
    pool_close_patcher.stop()

if __name__ == "__main__":
    unittest.main()
