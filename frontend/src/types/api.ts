export interface ResponseEnvelope<T> {
  success: boolean;
  data: T;
  metadata?: PaginationMetadata | null;
}

export interface PaginationMetadata {
  page: number;
  page_size: number;
  total_records: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface CompanyAnalytics {
  company: string;
  total_jobs: number;
  unique_locations: number;
  avg_salary_min: number | null;
  avg_salary_max: number | null;
  original_jobs_count: number;
  highest_paying_role: string | null;
  latest_posting: string | null;
  jobs_with_salary: number;
}

export interface SkillAnalytics {
  tag: string;
  job_demand_count: number;
  avg_salary_min: number | null;
  avg_salary_max: number | null;
  salary_premium: number | null;
  remote_jobs_count: number;
}

export interface GeographyAnalytics {
  country: string;
  region: string;
  jobs_count: number;
  avg_salary_min: number | null;
  avg_salary_max: number | null;
  company_count: number;
  remote_count: number;
  onsite_count: number;
  hybrid_count: number;
}

export interface SalaryAnalytics {
  salary_tier: string;
  jobs_count: number;
  avg_salary_min: number | null;
  avg_salary_max: number | null;
}

export interface TechnologyAnalytics {
  tech_tag: string;
  job_demand_count: number;
  avg_salary_min: number | null;
  avg_salary_max: number | null;
  top_company: string | null;
}

export interface HiringSummary {
  total_jobs: number;
  total_companies: number;
  total_locations: number;
  remote_jobs: number;
  remote_percentage: number;
  average_salary: number | null;
  median_salary: number | null;
  highest_salary: number | null;
  highest_paying_company: string | null;
  top_company: string | null;
  top_skill: string | null;
  top_country: string | null;
  jobs_with_salary: number;
  jobs_without_salary: number;
  generation_timestamp: string;
}

export interface DatasetFreshness {
  dataset: string;
  last_refresh: string;
  current_age: string;
  source_generation_timestamp: string;
  refresh_lag_minutes: number;
  status: string;
}

export interface ApiVersionInfo {
  version: string;
  git_commit: string;
  build_timestamp: string;
  python_version: string;
}
