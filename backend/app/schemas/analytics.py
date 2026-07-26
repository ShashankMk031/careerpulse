from datetime import datetime
from pydantic import BaseModel, Field

class CompanyAnalyticsOut(BaseModel):
    company: str = Field(description="Name of the company active in hiring.")
    total_jobs: int = Field(description="Total job openings posted.")
    unique_locations: int = Field(description="Number of distinct cities or regions where hiring is active.")
    avg_salary_min: float | None = Field(None, description="Average starting salary of the company's postings.")
    avg_salary_max: float | None = Field(None, description="Average maximum salary of the company's postings.")
    original_jobs_count: int = Field(description="Total jobs ingested originally before normalization.")
    highest_paying_role: str | None = Field(None, description="Job title with the highest listed salary range.")
    latest_posting: datetime | None = Field(None, description="Timestamp of the most recent job posting.")
    jobs_with_salary: int = Field(description="Count of jobs containing explicit salary range values.")

    class Config:
        from_attributes = True

class SkillAnalyticsOut(BaseModel):
    tag: str = Field(description="Normalized skill or technology tag.")
    job_demand_count: int = Field(description="Total jobs listing this tag as a requirement.")
    avg_salary_min: float | None = Field(None, description="Average minimum salary across postings with this tag.")
    avg_salary_max: float | None = Field(None, description="Average maximum salary across postings with this tag.")
    salary_premium: float | None = Field(None, description="Premium salary increment calculated for this tag.")
    remote_jobs_count: int = Field(description="Number of remote postings demanding this skill tag.")

    class Config:
        from_attributes = True

class GeographyAnalyticsOut(BaseModel):
    country: str = Field(description="Country or region classification (e.g. United States, Germany, Remote).")
    region: str = Field(description="City or region name.")
    jobs_count: int = Field(description="Number of job openings active in this region.")
    avg_salary_min: float | None = Field(None, description="Average minimum starting salary in this geography.")
    avg_salary_max: float | None = Field(None, description="Average maximum listed salary in this geography.")
    company_count: int = Field(description="Active company count recruiting in this geography.")
    remote_count: int = Field(description="Total remote jobs in this country/region.")
    onsite_count: int = Field(description="Total onsite jobs in this country/region.")
    hybrid_count: int = Field(description="Total hybrid jobs in this country/region.")

    class Config:
        from_attributes = True

class SalaryAnalyticsOut(BaseModel):
    salary_tier: str = Field(description="Salary range bin classification.")
    jobs_count: int = Field(description="Total postings falling into this salary bracket.")
    avg_salary_min: float | None = Field(None, description="Average lower bound salary inside this tier.")
    avg_salary_max: float | None = Field(None, description="Average upper bound salary inside this tier.")

    class Config:
        from_attributes = True

class TechnologyAnalyticsOut(BaseModel):
    tech_tag: str = Field(description="Name of the technology or framework.")
    job_demand_count: int = Field(description="Total postings citing this tech keyword.")
    avg_salary_min: float | None = Field(None, description="Average minimum salary for this technology.")
    avg_salary_max: float | None = Field(None, description="Average maximum salary for this technology.")
    top_company: str | None = Field(None, description="Name of the company hiring most heavily for this technology.")

    class Config:
        from_attributes = True

class HiringSummaryOut(BaseModel):
    total_jobs: int = Field(description="Combined job posting count.")
    total_companies: int = Field(description="Total active unique companies.")
    total_locations: int = Field(description="Total hiring locations.")
    remote_jobs: int = Field(description="Total postings flagging remote flexibility.")
    remote_percentage: float = Field(description="Ratio of remote jobs relative to total openings.")
    average_salary: float | None = Field(None, description="Overall average starting salary.")
    median_salary: float | None = Field(None, description="Overall median listed salary.")
    highest_salary: float | None = Field(None, description="Absolute highest salary value in the system.")
    highest_paying_company: str | None = Field(None, description="Company listing the highest salary range.")
    top_company: str | None = Field(None, description="Company with the most job postings.")
    top_skill: str | None = Field(None, description="Most highly demanded skill tag.")
    top_country: str | None = Field(None, description="Country with the highest job density.")
    jobs_with_salary: int = Field(description="Job postings listing salary statistics.")
    jobs_without_salary: int = Field(description="Job postings without salary details.")
    generation_timestamp: datetime = Field(description="Timestamp indicating when this pipeline execution ran.")

    class Config:
        from_attributes = True

class DatasetFreshnessOut(BaseModel):
    dataset: str = Field(description="Dataset name (e.g. company, skills, summary).")
    last_refresh: datetime = Field(description="Timestamp of the most recent database write.")
    current_age: str = Field(description="Textual representation of time elapsed since last refresh.")
    source_generation_timestamp: datetime = Field(description="Timestamp of Gold dataset parquet generation on S3.")
    refresh_lag_minutes: float = Field(description="Sync lag delta in minutes.")
    status: str = Field(description="Freshness tag (FRESH or STALE).")

    class Config:
        from_attributes = True
