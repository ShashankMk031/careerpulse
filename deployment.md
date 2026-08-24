# CareerPulse Production Deployment Guide

This document describes how to deploy the CareerPulse job market intelligence platform to production environments.

---

## 1. Prerequisites
Ensure the target server environment has the following tools installed:
* **Docker** (v24.0 or higher)
* **Docker Compose** (v2.20 or higher)
* **make** utility (for automated shorthand tasks)

---

## 2. Environment Configuration
Copy the provided `.env.example` templates into active `.env` configuration files:

```bash
# In the repository root
cp .env.example .env

# In the backend directory
cp backend/.env.example backend/.env

# In the frontend directory
cp frontend/.env.example frontend/.env
```

### Essential Production Variables
Configure the following variables inside `backend/.env` for production workloads:
* `APP_ENV`: Set to `production` (disables debug logging and API Swagger documentation).
* `LOG_LEVEL`: Set to `info` or `warning` (enables structured JSON logging formatters).
* `POSTGRES_DB`: Production PostgreSQL database name.
* `POSTGRES_USER`: Authorized Postgres connection user.
* `POSTGRES_PASSWORD`: Strong password string.
* `POSTGRES_HOST`: Endpoint address of the RDS PostgreSQL database instance.

---

## 3. Production Deployment Commands

### Building Pinned Docker Images
To build the optimized Docker images (using pinned base layers and multi-stage Node/Python builders):
```bash
make build
```
This builds both development targets and the production image configurations.

### Starting the Production Stack
To run the production stack (Nginx proxy, FastAPI backend, and PostgreSQL database) in background daemon mode:
```bash
docker compose -f docker-compose.prod.yml up -d
```
*Note: The production cluster configures automatic restart policies (`restart: unless-stopped`) and runs the Nginx frontend as a read-only container (`read_only: true`) using internal `tmpfs` RAM paths for maximum container hardening.*

### Stopping the Production Stack
To tear down the active production container stack and preserve database volumes:
```bash
docker compose -f docker-compose.prod.yml down
```

---

## 4. Monitoring & Verification

### Container Statuses
Check running container health status flags:
```bash
docker compose -f docker-compose.prod.yml ps
```

### Logs Auditing
Inspect backend API and Nginx proxy logs using structured JSON formatting:
```bash
docker compose -f docker-compose.prod.yml logs -f
```

### Gateway Health Audits
Confirm Nginx is actively proxying traffic and FastAPI resolves database pools:
```bash
# Gateway Healthcheck
curl -i http://localhost/health

# Serving Layer Summary Metrics
curl -i http://localhost/api/v1/summary
```
Expected output should return a `200 OK` header along with a JSON envelope:
```json
{
  "success": true,
  "data": { ... },
  "metadata": { ... }
}
```
