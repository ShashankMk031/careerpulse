from dataclasses import dataclass
from datetime import datetime

@dataclass
class CompanyAnalytics:
    company: str
    total_jobs: int
    unique_locations: int
    avg_salary_min: float | None
    avg_salary_max: float | None
    original_jobs_count: int
    highest_paying_role: str | None
    latest_posting: datetime | None
    jobs_with_salary: int
    created_at: datetime
    updated_at: datetime

@dataclass
class SkillAnalytics:
    tag: str
    job_demand_count: int
    avg_salary_min: float | None
    avg_salary_max: float | None
    salary_premium: float | None
    remote_jobs_count: int
    created_at: datetime
    updated_at: datetime

@dataclass
class GeographyAnalytics:
    country: str
    region: str
    jobs_count: int
    avg_salary_min: float | None
    avg_salary_max: float | None
    company_count: int
    remote_count: int
    onsite_count: int
    hybrid_count: int
    created_at: datetime
    updated_at: datetime

@dataclass
class SalaryAnalytics:
    salary_tier: str
    jobs_count: int
    avg_salary_min: float | None
    avg_salary_max: float | None
    created_at: datetime
    updated_at: datetime

@dataclass
class TechnologyAnalytics:
    tech_tag: str
    job_demand_count: int
    avg_salary_min: float | None
    avg_salary_max: float | None
    top_company: str | None
    created_at: datetime
    updated_at: datetime

@dataclass
class HiringSummary:
    id: int
    total_jobs: int
    total_companies: int
    total_locations: int
    remote_jobs: int
    remote_percentage: float
    average_salary: float | None
    median_salary: float | None
    highest_salary: float | None
    highest_paying_company: str | None
    top_company: str | None
    top_skill: str | None
    top_country: str | None
    jobs_with_salary: int
    jobs_without_salary: int
    generation_timestamp: datetime
    created_at: datetime
    updated_at: datetime

@dataclass
class DatasetFreshness:
    dataset: str
    last_refresh: datetime
    current_age: str  # Interval represented as string
    source_generation_timestamp: datetime
    refresh_lag_minutes: float
    status: str
