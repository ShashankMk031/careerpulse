# Data Dictionary: Silver Layer (Cleaned & Standardized Data)

## 1. Operational Metadata
* **Layer:** Silver (Cleaned / Standardized)
* **Format:** Snappy-compressed Parquet (columnar, optimized for query performance)
* **Write Frequency:** Ingestion-triggered batch (AWS Glue Job `cp_dev_silver_etl`)
* **Primary Writer:** PySpark Glue ETL
* **Primary Reader:** Athena Analytics, Gold Orchestrator (`cp_dev_gold_etl`)
* **S3 URI Prefix:** `s3://cp-dev-datalake-321422008826/silver/source=remoteok/`
* **Partitioning Keys:** `year` (YYYY), `month` (MM), `day` (DD)

## 2. Table Schema: `cp_dev_catalog.remoteok_silver`

| Column Name | Hive Datatype | Description | Nullable? | Normalization Rules |
| :--- | :--- | :--- | :---: | :--- |
| `id` | `bigint` | Unique identifier for the job post | No | Deduped using window functions (ranking by latest epoch). |
| `slug` | `string` | URL-friendly slug representing the listing | Yes | String trimmed. |
| `epoch` | `bigint` | Unix timestamp of posting publication | Yes | Extracted as raw integer. |
| `date_posted` | `timestamp` | ISO-8859 standardized UTC timestamp | Yes | Cast from raw ISO-8601 string fields. |
| `company` | `string` | Name of the hiring organization | No | Trimmed, UTF-8 Mojibake healed. |
| `company_logo` | `string` | URL path to the company's logo | Yes | String trimmed. |
| `position` | `string` | Job title or role name | No | Trimmed, UTF-8 Mojibake healed. |
| `tags` | `array<string>`| Array of clean lowercase skill tags | Yes | Trimmed and case-lowered. |
| `description` | `string` | Plain text or HTML job description | Yes | Retained as-is for search indexing. |
| `location` | `string` | Raw location string | Yes | String trimmed. |
| `country` | `string` | Standardized country string | No | Parsed into standard classes: `USA`, `Canada`, `UK`, `Remote`, or specific location name. Defaults to `Unknown`. |
| `region` | `string` | Workspace mode classification | No | Mapped to `Remote`, `hybrid`, or `onsite`. |
| `remote_flag` | `boolean` | Flag indicating if role is fully remote | No | Derived based on keywords in location string (e.g. "remote"). |
| `apply_url` | `string` | Direct link to submit applications | Yes | String trimmed. |
| `salary_min` | `int` | Standardized minimum salary (annual USD) | Yes | Validated > 0; non-positive values mapped to `NULL`. |
| `salary_max` | `int` | Standardized maximum salary (annual USD) | Yes | Validated > 0; non-positive values mapped to `NULL`. |
| `logo` | `string` | Fallback logo image path URL | Yes | String trimmed. |
| `url` | `string` | Fallback job post link URL | Yes | String trimmed. |
| `original` | `boolean` | Flag indicating primary source post | Yes | Cast to standard boolean format. |
| `year` | `string` | Partition column (Ingestion Year) | Partition | Format: `YYYY` |
| `month` | `string` | Partition column (Ingestion Month) | Partition | Format: `MM` |
| `day` | `string` | Partition column (Ingestion Day) | Partition | Format: `DD` |

## 3. Reference Verification Queries

```sql
-- Query clean geography distribution
SELECT country, region, count(*) as active_listings
FROM cp_dev_catalog.remoteok_silver
GROUP BY country, region
ORDER BY active_listings DESC;

-- Verify NULL mapping for missing salary listings
SELECT id, company, position, salary_min, salary_max
FROM cp_dev_catalog.remoteok_silver
WHERE salary_min IS NULL
LIMIT 5;
```

## 4. Known Data Limitations
* Salary ranges rely on API provider entry. Unspecified salary rates are mapped to `NULL` to avoid skews.
* Country extraction is heuristic-based and relies on accurate geo-strings from raw API postings.
