# Data Dictionary: Gold Layer (Analytical Datasets)

## 1. Operational Metadata
* **Layer:** Gold (Aggregated / Business-ready)
* **Format:** Snappy-compressed Parquet (uncut flat schemas optimized for BI tools / Athena)
* **Write Frequency:** Triggered batch execution (Glue Job `cp_dev_gold_etl`)
* **Primary Writer:** PySpark Glue ETL (Orchestrator Pattern)
* **Primary Reader:** BI Dashboards, Business Analysts, downstream consumers
* **S3 URI Prefix:** `s3://cp-dev-datalake-321422008826/gold/<dataset_name>/`
* **Auto-Cataloging:** Auto-discovered and registered by AWS Glue Crawler `cp_dev_gold_crawler`

---

## 2. Table Definitions

### A. Company Analytics (`gold_company`)
Aggregates job postings and wage indices grouped by hiring organizations.

| Column Name | Datatype | Description |
| :--- | :--- | :--- |
| `company` | `string` | Name of hiring company |
| `total_jobs` | `bigint` | Total job postings registered |
| `unique_locations` | `bigint` | Count of unique location centers |
| `avg_salary_min` | `double` | Average minimum salary offered (USD) |
| `avg_salary_max` | `double` | Average maximum salary offered (USD) |
| `original_jobs_count` | `bigint` | Count of primary original posts |
| `highest_paying_role` | `string` | Job title of role offering max salary |
| `latest_posting` | `timestamp` | Timestamp of latest listing publication |
| `jobs_with_salary` | `bigint` | Count of job listings containing salary |

---

### B. Skills Analytics (`gold_skills`)
Tracks developer skill demand metrics and salary premiums.

| Column Name | Datatype | Description |
| :--- | :--- | :--- |
| `tag` | `string` | Standardized skill name (lowercase) |
| `job_demand_count` | `bigint` | Total job posts requiring this skill |
| `avg_salary_min` | `double` | Average minimum salary for this skill |
| `avg_salary_max` | `double` | Average maximum salary for this skill |
| `salary_premium` | `double` | Premium difference over market average |
| `remote_jobs_count` | `bigint` | Count of remote listings requiring this skill |

---

### C. Geography Analytics (`gold_geography`)
Tracks location splits and geographic hiring indices.

| Column Name | Datatype | Description |
| :--- | :--- | :--- |
| `country` | `string` | Standardized country location name |
| `region` | `string` | Work mode region: `Remote`, `hybrid`, `onsite` |
| `jobs_count` | `bigint` | Total job listings in this region |
| `avg_salary_min` | `double` | Average minimum salary offered |
| `avg_salary_max` | `double` | Average maximum salary offered |
| `company_count` | `bigint` | Unique companies active in this geography |
| `remote_count` | `bigint` | Count of fully remote jobs |
| `onsite_count` | `bigint` | Count of onsite jobs |
| `hybrid_count` | `bigint` | Count of hybrid jobs |

---

### D. Salary Analytics (`gold_salary`)
Maps distributions across salary tiers.

| Column Name | Datatype | Description |
| :--- | :--- | :--- |
| `salary_tier` | `string` | Bracket label (e.g. "Senior (100k-150k)") |
| `jobs_count` | `bigint` | Total listings in this bracket |
| `avg_salary_min` | `double` | Average minimum salary in tier |
| `avg_salary_max` | `double` | Average maximum salary in tier |

---

### E. Technology Analytics (`gold_technology`)
Maps technology fields dynamically.

| Column Name | Datatype | Description |
| :--- | :--- | :--- |
| `tech_tag` | `string` | Technology tag name |
| `job_demand_count` | `bigint` | Count of jobs referencing technology |
| `avg_salary_min` | `double` | Average minimum salary |
| `avg_salary_max` | `double` | Average maximum salary |
| `top_company` | `string` | Principal company hiring for this tech |

---

### F. Hiring Summary (`gold_summary`)
Dashboard KPIs aggregated across all processed postings.

| Column Name | Datatype | Description |
| :--- | :--- | :--- |
| `total_jobs` | `bigint` | Overall count of processed postings |
| `total_companies` | `bigint` | Overall unique companies hiring |
| `total_locations` | `bigint` | Overall unique locations listed |
| `remote_jobs` | `bigint` | Total fully remote listings |
| `remote_percentage` | `double` | Percentage share of remote listings |
| `average_salary` | `double` | Average overall salary |
| `median_salary` | `double` | Median overall salary |
| `highest_salary` | `double` | Peak maximum salary across data |
| `highest_paying_company` | `string` | Company offering the highest salary |
| `top_company` | `string` | Company listing the most jobs |
| `top_skill` | `string` | Most demanded skill tag |
| `top_country` | `string` | Country listing the most jobs |
| `jobs_with_salary` | `bigint` | Count of listings specifying salaries |
| `jobs_without_salary` | `bigint` | Count of listings without salaries |
| `generation_timestamp` | `timestamp` | Time of pipeline dataset creation |

---

## 3. Downstream Consumers
* **CareerPulse FastAPI backend:** Serves REST APIs powering UI widgets.
* **Streamlit Executive Dashboard:** Renders charts, maps, and tables for users.
