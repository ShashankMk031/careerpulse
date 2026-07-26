# serving Layer API Architecture

This document outlines the architectural blueprint, design patterns, request lifecycle, and data flow implemented in Sprint 7 for the CareerPulse serving layer backend.

---

## 1. Architectural Blueprint (Layered Design)

The backend conforms to a strict layered design to decouple client requests, business logic orchestration, and raw database access:

```
                  ┌──────────────────────┐
                  │      HTTP Client     │
                  └──────────┬───────────┘
                             │ (JSON)
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │ FastAPI HTTP Controllers (routers/)                    │
  │ - Parameter Parsing, Swagger docs, Pydantic envelopes │
  └──────────────────────────┬─────────────────────────────┘
                             │ (Pydantic / Method args)
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │ Service Orchestrator Layer (services/)                 │
  │ - Business rules, range validations, exception triggers│
  └──────────────────────────┬─────────────────────────────┘
                             │ (Connection, method parameters)
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │ Repository Data Layer (repositories/)                  │
  │ - Parameterized Raw SQL, mapping rows to Dataclasses   │
  └──────────────────────────┬─────────────────────────────┘
                             │ (SQL queries)
                             ▼
                  ┌──────────────────────┐
                  │    PostgreSQL RDS    │
                  └──────────────────────┘
```

* **Routers (`backend/app/routers/`):** Define REST routes, handle HTTP status codes, configure OpenAPI docs schemas, validate paging limits via dependencies, and map returned objects into the generic JSON envelope.
* **Services (`backend/app/services/`):** Implement business logical checks (e.g. page parameter checks, non-negative constraint checking), coordinate data operations, and raise structured domain exceptions when entities do not exist.
* **Repositories (`backend/app/repositories/`):** Direct database accessor. Writes clean, parameterized PostgreSQL commands, queries tables/views, maps rows to typed python dataclasses, and enforces static type analysis.

---

## 2. Request Lifecycle

Every HTTP request undergoes a structured transactional flow:

1. **Incoming Request:** Client sends an HTTP request.
2. **Middleware Interception:** `RequestLoggingMiddleware` assigns a UUID4 `request_id`, attaches it to the request state, and starts execution timers.
3. **Routing & Injection:** Router inspects parameters, runs dependency validation (e.g. checking page ranges), and requests a connection dependency checkout (`get_db`) from the global `ThreadedConnectionPool`.
4. **Service execution:** Service checks business bounds and raises a custom `AppException` (e.g. `NotFoundException`) if entities are missing.
5. **Database Transaction:** Repository executes parameterized queries, parses results into dataclasses, and returns them.
6. **Transaction Cleanup:** The database connection context manager automatically commits the query on successful exit (or executes rollback if database exceptions occur) and puts the connection back in the pool.
7. **Response Serialization:** Router intercepts the typed dataclass and wraps it inside `ResponseEnvelope` with `success=True`.
8. **Logging Middleware Exit:** Middleware calculates total processing duration in milliseconds, appends `X-Request-ID` and `X-Process-Time-MS` response headers, writes structured terminal logs, and returns JSON.

---

## 3. Dependency Injection

We leverage FastAPI's dependency injection (`Depends`) to maintain lifecycle safety:
* **`get_db` Dependency:** Exposes active database transactions. Encapsulates checking out and releasing connections back to the thread-safe `ThreadedConnectionPool`. By wrapping database transactions inside a context manager dependency, we eliminate connection leaks.
* **`get_pagination_params` Dependency:** Validates that page inputs are valid ($page \ge 1$) and limits results sizes to a maximum of 100 per page to protect backend resources.

---

## 4. Connection Pooling

* **Pool Implementation:** We reuse the project-wide thread-safe `ThreadedConnectionPool` from `psycopg2.pool`, dynamically initialized on server startup and cleanly terminated on server shutdown during uvicorn lifecycles.
* **API Impact:** Reusing connections from a warm pool avoids the costly network round trips of SSL handshakes and fork process spawning inside PostgreSQL, bringing connection acquisition time down from **~40-50ms** to **`0.02ms`**.

---

## 5. Standardized Error Handling & Exception Management

We register global exception handlers on the FastAPI app context to map custom application errors to structured, readable JSON response formats:

```json
{
  "success": false,
  "error": "Error description message text",
  "error_code": "ERROR_CODE_IDENTIFIER"
}
```

### Exception Mappings:
| Exception Class | HTTP Status | Error Code | Description |
| :--- | :--- | :--- | :--- |
| `ValidationException` | `400 Bad Request` | `BAD_REQUEST` / `VALIDATION_ERROR` | Raised when input parameters fail constraint check bounds. |
| `NotFoundException` | `404 Not Found` | `RESOURCE_NOT_FOUND` | Raised when single resource queries return empty. |
| `DatabaseException` | `500 Server Error` | `DATABASE_ERROR` | Raised on underlying query execution failure. Hides stack traces. |
| `AppException` | `500 Server Error` | `INTERNAL_SERVER_ERROR` | Generic server fallback error. |

---

## 6. Response Compression (GZip)

We register `GZipMiddleware` in the application routing pipeline with a minimum compression threshold size of `1024` bytes.

### Why Response Compression Improves API Performance:
* **Bandwidth Savings:** Highly redundant analytical JSON documents (like paginated skill tags or company stats) can be compressed by up to **70-80%** using the DEFLATE algorithm.
* **Reduced Time-to-First-Byte (TTFB):** Transferring significantly fewer bytes over the network mitigates TCP slow-start and packet loss, especially over mobile connections or high-latency WANs, yielding major speed benefits.

---

## 7. Cache-Control Headers

Standard HTTP `Cache-Control` response headers are appended to the response of analytical endpoints:
* **Summary Endpoint:** Configured with `max-age` set to `CACHE_MAX_AGE_SUMMARY` (default: 5 minutes / `300s`).
* **Skills/Tech Analytics:** Configured with `max-age` set to `CACHE_MAX_AGE_ANALYTICS` (default: 1 hour / `3600s`).

This enables web browsers, CDN edge nodes, and local caches to reuse responses directly without hitting the application servers.

---

## 8. Query Timing & Structured JSON Logging

* **Async-Safe Tracing (`contextvars`):** We declare `db_duration_ctx` as a `ContextVar` to trace cumulative database query execution times per request thread without mutating method signatures.
* **Repository Decoration:** Static query methods inside repositories are decorated with `@track_db_time` to automatically record database execution times.
* **Structured Logging format:** Plain text console output is replaced with JSON structured logs mapping the following parameters:
  ```json
  {
    "timestamp": "2026-07-25T19:44:21.784431+00:00",
    "request_id": "3bfd3568-e80e-47a0-9be0-9a41cb575fb0",
    "client_ip": "testclient",
    "method": "GET",
    "path": "/version",
    "status": 200,
    "duration": 10.76,
    "database_duration": 0.00,
    "api_duration": 10.76
  }
  ```
  This cleanly isolates database latency from FastAPI routing/serialization overhead, optimizing debugging and telemetry tracking.

---

## 9. Fail-Fast Configuration Validation

The application constructor (`Settings`) validates environment variables upon boot (checking for RDS hosts or local equivalents). If mandatory environment configuration is missing, the application raises `ValueError` immediately and refuses to start, preventing running in a corrupt state.

