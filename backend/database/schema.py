"""
Defines the explicit DDL schema queries, constraints, and indexes for CareerPulse Serving layer.
"""

CREATE_SCHEMA_QUERY = "CREATE SCHEMA IF NOT EXISTS serving;"

# Explicit DDL statements for normalized serving tables with CHECK constraints
CREATE_TABLES_QUERIES = [
    # 1. Company Analytics
    """
    CREATE TABLE IF NOT EXISTS serving.company_analytics (
        company VARCHAR(255) PRIMARY KEY,
        total_jobs BIGINT NOT NULL CHECK (total_jobs >= 0),
        unique_locations INTEGER NOT NULL CHECK (unique_locations >= 0),
        avg_salary_min DOUBLE PRECISION,
        avg_salary_max DOUBLE PRECISION,
        original_jobs_count BIGINT NOT NULL CHECK (original_jobs_count >= 0),
        highest_paying_role VARCHAR(255),
        latest_posting TIMESTAMP WITH TIME ZONE,
        jobs_with_salary BIGINT NOT NULL CHECK (jobs_with_salary >= 0),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 2. Skills Analytics
    """
    CREATE TABLE IF NOT EXISTS serving.skills_analytics (
        tag VARCHAR(100) PRIMARY KEY,
        job_demand_count BIGINT NOT NULL CHECK (job_demand_count >= 0),
        avg_salary_min DOUBLE PRECISION,
        avg_salary_max DOUBLE PRECISION,
        salary_premium DOUBLE PRECISION,
        remote_jobs_count BIGINT NOT NULL CHECK (remote_jobs_count >= 0),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 3. Geography Analytics
    """
    CREATE TABLE IF NOT EXISTS serving.geography_analytics (
        country VARCHAR(255) NOT NULL,
        region VARCHAR(100) NOT NULL,
        jobs_count BIGINT NOT NULL CHECK (jobs_count >= 0),
        avg_salary_min DOUBLE PRECISION,
        avg_salary_max DOUBLE PRECISION,
        company_count BIGINT NOT NULL CHECK (company_count >= 0),
        remote_count BIGINT NOT NULL CHECK (remote_count >= 0),
        onsite_count BIGINT NOT NULL CHECK (onsite_count >= 0),
        hybrid_count BIGINT NOT NULL CHECK (hybrid_count >= 0),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (country, region)
    );
    """,
    # 4. Salary Analytics
    """
    CREATE TABLE IF NOT EXISTS serving.salary_analytics (
        salary_tier VARCHAR(100) PRIMARY KEY,
        jobs_count BIGINT NOT NULL CHECK (jobs_count >= 0),
        avg_salary_min DOUBLE PRECISION,
        avg_salary_max DOUBLE PRECISION,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 5. Technology Analytics
    """
    CREATE TABLE IF NOT EXISTS serving.technology_analytics (
        tech_tag VARCHAR(100) PRIMARY KEY,
        job_demand_count BIGINT NOT NULL CHECK (job_demand_count >= 0),
        avg_salary_min DOUBLE PRECISION,
        avg_salary_max DOUBLE PRECISION,
        top_company VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 6. Hiring Summary (latest snapshot dashboard representation)
    """
    CREATE TABLE IF NOT EXISTS serving.hiring_summary (
        id SERIAL PRIMARY KEY,
        total_jobs BIGINT NOT NULL CHECK (total_jobs >= 0),
        total_companies BIGINT NOT NULL CHECK (total_companies >= 0),
        total_locations BIGINT NOT NULL CHECK (total_locations >= 0),
        remote_jobs BIGINT NOT NULL CHECK (remote_jobs >= 0),
        remote_percentage DOUBLE PRECISION NOT NULL CHECK (remote_percentage BETWEEN 0 AND 100),
        average_salary DOUBLE PRECISION,
        median_salary DOUBLE PRECISION,
        highest_salary DOUBLE PRECISION,
        highest_paying_company VARCHAR(255),
        top_company VARCHAR(255),
        top_skill VARCHAR(100),
        top_country VARCHAR(255),
        jobs_with_salary BIGINT NOT NULL CHECK (jobs_with_salary >= 0),
        jobs_without_salary BIGINT NOT NULL CHECK (jobs_without_salary >= 0),
        generation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 7. Metadata Load History
    """
    CREATE TABLE IF NOT EXISTS serving.load_metadata (
        id SERIAL PRIMARY KEY,
        pipeline_execution_id VARCHAR(100) NOT NULL,
        source_pipeline_execution_id VARCHAR(100),
        table_name VARCHAR(100) NOT NULL,
        dataset_name VARCHAR(100) NOT NULL,
        load_type VARCHAR(50) NOT NULL CHECK (load_type IN ('UPSERT', 'REPLACE')),
        status VARCHAR(20) NOT NULL CHECK (status IN ('SUCCESS', 'FAILED')),
        records_loaded BIGINT NOT NULL,
        records_failed BIGINT NOT NULL,
        rows_inserted BIGINT NOT NULL DEFAULT 0,
        rows_updated BIGINT NOT NULL DEFAULT 0,
        load_duration_ms BIGINT NOT NULL,
        error_message TEXT,
        start_time TIMESTAMP WITH TIME ZONE NOT NULL,
        end_time TIMESTAMP WITH TIME ZONE NOT NULL,
        generation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        rows_per_second DOUBLE PRECISION,
        bytes_processed BIGINT,
        database_write_rate DOUBLE PRECISION,
        connection_wait_time_ms DOUBLE PRECISION,
        transaction_duration_ms DOUBLE PRECISION,
        retry_count INTEGER DEFAULT 0,
        refresh_lag_minutes DOUBLE PRECISION,
        load_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
]

# Explicit index definitions for sorting and filtering optimization
CREATE_INDEX_QUERIES = [
    "CREATE INDEX IF NOT EXISTS idx_company_total_jobs ON serving.company_analytics(total_jobs DESC);",
    "CREATE INDEX IF NOT EXISTS idx_skills_demand ON serving.skills_analytics(job_demand_count DESC);",
    "CREATE INDEX IF NOT EXISTS idx_tech_demand ON serving.technology_analytics(job_demand_count DESC);",
    "CREATE INDEX IF NOT EXISTS idx_geo_jobs_count ON serving.geography_analytics(jobs_count DESC);"
]

# Explicit analytical views for API queries
CREATE_VIEW_QUERIES = [
    """
    CREATE OR REPLACE VIEW serving.v_top_companies AS
    SELECT company, total_jobs, unique_locations, highest_paying_role, latest_posting
    FROM serving.company_analytics
    ORDER BY total_jobs DESC;
    """,
    """
    CREATE OR REPLACE VIEW serving.v_top_skills AS
    SELECT tag, job_demand_count, salary_premium, remote_jobs_count
    FROM serving.skills_analytics
    ORDER BY job_demand_count DESC;
    """,
    """
    CREATE OR REPLACE VIEW serving.v_top_countries AS
    SELECT country, SUM(jobs_count) AS total_jobs_count, SUM(company_count) AS active_companies_count
    FROM serving.geography_analytics
    WHERE country != 'Remote' AND country IS NOT NULL
    GROUP BY country
    ORDER BY total_jobs_count DESC;
    """,
    """
    CREATE OR REPLACE VIEW serving.v_dashboard_summary AS
    SELECT total_jobs, total_companies, total_locations, remote_jobs, remote_percentage,
           average_salary, median_salary, highest_salary, highest_paying_company,
           top_company, top_skill, top_country, generation_timestamp
    FROM serving.hiring_summary
    ORDER BY generation_timestamp DESC
    LIMIT 1;
    """,
    """
    CREATE OR REPLACE VIEW serving.v_dataset_status AS
    WITH latest_loads AS (
        SELECT 
            dataset_name,
            load_timestamp AS last_successful_refresh,
            generation_timestamp AS source_generation_timestamp,
            refresh_lag_minutes,
            status,
            ROW_NUMBER() OVER (PARTITION BY dataset_name ORDER BY load_timestamp DESC) as rn
        FROM serving.load_metadata
        WHERE status = 'SUCCESS'
    )
    SELECT 
        dataset_name AS dataset,
        last_successful_refresh AS last_refresh,
        NOW() - last_successful_refresh AS current_age,
        source_generation_timestamp,
        refresh_lag_minutes,
        CASE 
            WHEN (NOW() - last_successful_refresh) < INTERVAL '2 hours' THEN 'FRESH'
            ELSE 'STALE'
        END AS status
    FROM latest_loads
    WHERE rn = 1;
    """
]

