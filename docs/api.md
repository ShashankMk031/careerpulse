# CareerPulse REST API Reference

## 1. Overview

The CareerPulse REST API is built on FastAPI and Python 3.12, providing high-performance, low-latency access to the PostgreSQL serving layer. All analytical endpoints return data within standardized response envelopes, include request profiling headers, and enforce explicit HTTP caching policies.

- **Base URL (Local Development):** `http://127.0.0.1:8000`
- **Interactive Documentation:**
  - Swagger UI: `http://127.0.0.1:8000/docs`
  - ReDoc: `http://127.0.0.1:8000/redoc`
  - OpenAPI Specification: `http://127.0.0.1:8000/openapi.json`

---

## 2. Standard Response Format

Every API endpoint wraps its payload inside a standard envelope.

### 2.1 Success Response (`ResponseEnvelope[T]`)
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "page": 1,
    "page_size": 20,
    "total_records": 175,
    "total_pages": 9,
    "has_next": true,
    "has_previous": false
  }
}
```
*Note: `metadata` is included on all paginated endpoints; singular resource endpoints omit `metadata`.*

### 2.2 Error Response (`ErrorEnvelope`)
```json
{
  "success": false,
  "error": "Detailed human-readable error description",
  "error_code": "VALIDATION_ERROR"
}
```

### 2.3 Custom Telemetry Headers
Every response includes profiling and correlation headers:
- `X-Request-ID`: UUIDv4 uniquely identifying the incoming request for distributed tracing.
- `X-Process-Time-MS`: Total roundtrip elapsed duration inside FastAPI (in milliseconds).
- `X-Database-Time-MS`: Cumulative time spent executing SQL queries in the PostgreSQL pool.

---

## 3. Endpoints Reference

### 3.1 System & Telemetry Endpoints

#### `GET /health`
Validates process liveness and active database connectivity readiness by executing a lightweight ping (`SELECT 1;`) through the connection pool.

- **Response Model:** `ResponseEnvelope[dict]`
- **Sample Request:**
  ```bash
  curl -s http://127.0.0.1:8000/health
  ```
- **Sample Response:**
  ```json
  {
    "success": true,
    "data": {
      "status": "healthy",
      "database": "connected"
    }
  }
  ```

#### `GET /metrics`
Returns dataset sync telemetry and data freshness metrics from the `serving.v_dataset_status` database view.

- **Response Model:** `ResponseEnvelope[list[DatasetFreshnessOut]]`
- **Sample Response:**
  ```json
  {
    "success": true,
    "data": [
      {
        "dataset": "GOLD_COMPANY",
        "last_refresh": "2026-09-20T17:50:56Z",
        "current_age": "2h 15m",
        "refresh_lag_minutes": 135.2,
        "status": "Fresh"
      }
    ]
  }
  ```

#### `GET /version`
Returns active application version, Git commit SHA, build timestamp, and runtime environment.

- **Response Model:** `ResponseEnvelope[dict]`
- **Sample Response:**
  ```json
  {
    "success": true,
    "data": {
      "version": "1.0.0",
      "git_commit": "c0808c017e",
      "build_timestamp": "2026-07-25T18:17:00Z",
      "python_version": "3.12.9"
    }
  }
  ```

---

### 3.2 Analytical Endpoints (`/api/v1`)

#### `GET /api/v1/summary`
Returns high-level executive KPIs representing the current active hiring snapshot.

- **Cache-Control:** `public, max-age=300` (5 minutes)
- **Response Model:** `ResponseEnvelope[HiringSummaryOut]`
- **Sample Response:**
  ```json
  {
    "success": true,
    "data": {
      "total_jobs": 99,
      "total_companies": 93,
      "total_locations": 58,
      "remote_jobs": 8,
      "remote_percentage": 8.08,
      "average_salary": 161966.64,
      "median_salary": 120000.0,
      "highest_salary": 750000.0,
      "highest_paying_company": "Interaction Design Foundation",
      "top_company": "Growth Org",
      "top_skill": "TypeScript",
      "top_country": "United States",
      "jobs_with_salary": 14,
      "jobs_without_salary": 85,
      "generation_timestamp": "2026-09-19T10:28:48Z"
    }
  }
  ```

#### `GET /api/v1/companies`
Returns a paginated list of hiring companies with location counts, salary spreads, and latest job postings.

- **Query Parameters:**
  - `page` *(int, default: 1)*: Page number ($\ge 1$).
  - `page_size` *(int, default: 20)*: Page limit (1–100).
  - `sort_by` *(string, default: "company")*: Sort column (`company`, `total_jobs`, `unique_locations`, `latest_posting`).
  - `sort_order` *(string, default: "asc")*: Sort direction (`asc`, `desc`).
  - `search` *(string, optional)*: Partial case-insensitive match on company name.
  - `min_jobs` *(int, optional)*: Filter for companies with at least $N$ listings.
- **Sample Request:**
  ```bash
  curl -s "http://127.0.0.1:8000/api/v1/companies?page=1&page_size=2&sort_by=total_jobs&sort_order=desc"
  ```
- **Sample Response:**
  ```json
  {
    "success": true,
    "data": [
      {
        "company": "Re Lytics Hire",
        "total_jobs": 6,
        "unique_locations": 2,
        "avg_salary_min": 150000.0,
        "avg_salary_max": 250000.0,
        "original_jobs_count": 0,
        "highest_paying_role": "Senior Cloud Architect",
        "latest_posting": "2026-09-19T08:12:00Z",
        "jobs_with_salary": 2
      }
    ],
    "metadata": {
      "page": 1,
      "page_size": 2,
      "total_records": 175,
      "total_pages": 88,
      "has_next": true,
      "has_previous": false
    }
  }
  ```

#### `GET /api/v1/companies/{company}`
Returns detailed analytics for a single company by name.

- **Path Parameter:** `company` (string, URL-encoded company name).
- **Status Codes:** `200 OK`, `404 Not Found`.

#### `GET /api/v1/skills`
Returns paginated technical skill tag competencies, sorted by job demand or compensation premiums.

- **Cache-Control:** `public, max-age=3600` (1 hour)
- **Query Parameters:**
  - `page`, `page_size`: Pagination bounds.
  - `sort_by` *(string, default: "job_demand_count")*: Sort column (`tag`, `job_demand_count`, `salary_premium`, `remote_jobs_count`).
  - `sort_order` *(string, default: "desc")*: Sort direction (`asc`, `desc`).
  - `search` *(string, optional)*: Tag search query.
  - `min_demand` *(int, optional)*: Minimum job demand threshold.

#### `GET /api/v1/technology`
Returns tech stack categorization and tooling demand analytics.

- **Cache-Control:** `public, max-age=3600` (1 hour)
- **Query Parameters:**
  - `page`, `page_size`, `sort_by`, `sort_order`, `search`.

#### `GET /api/v1/geography`
Returns country and regional geographic distribution records.

- **Query Parameters:**
  - `country` *(string, optional)*: Filter by exact country name.
  - `remote` *(bool, optional)*: Filter remote (`true`) vs onsite (`false`).
  - `sort_by` *(string, default: "jobs_count")*: Sort column (`country`, `region`, `jobs_count`, `company_count`).
  - `sort_order` *(string, default: "desc")*: Sort direction (`asc`, `desc`).

#### `GET /api/v1/salary`
Returns job distributions categorized across standard salary bracket tiers.

- **Response Model:** `ResponseEnvelope[list[SalaryAnalyticsOut]]`
- **Tiers Returned:**
  - `Entry (< 50k)`
  - `Mid (50k-100k)`
  - `Staff (150k+)`
  - `Not Specified`

---

## 4. Error Codes & Handling

| HTTP Status | Error Code | Description |
| :--- | :--- | :--- |
| `400 Bad Request` | `VALIDATION_ERROR` | Request parameter failed constraint checks (e.g. `page < 1` or `page_size > 100`). |
| `404 Not Found` | `NOT_FOUND` | Requested entity does not exist (e.g. unknown company name). |
| `500 Internal Error`| `DATABASE_ERROR` | Database transaction or connection error occurred. Stack traces are masked in production. |
| `500 Internal Error`| `UNHANDLED_SERVER_ERROR` | Uncaught server exception. Masked unless `API_DEBUG=true`. |
