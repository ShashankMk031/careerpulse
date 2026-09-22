# CareerPulse Production Deployment Guide

## 1. Overview

This guide details the deployment procedures for CareerPulse across two primary topologies:
1. **Containerized Production Stack (Docker Compose + Nginx):** Suitable for single-instance VM deployments (AWS EC2, Lightsail, or on-premises servers).
2. **Cloud-Native AWS Deployment:** Deploying the data pipeline across managed AWS serverless and relational services (S3, Glue, Athena, RDS PostgreSQL, ECS/Fargate).

---

## 2. Environment Variable Configuration

All services are configured using environment variables. Before deploying, initialize your environment files:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### Complete Environment Variable Matrix

| Variable | Scope | Required | Default | Description |
| :--- | :--- | :---: | :--- | :--- |
| `APP_ENV` | Global / Backend | Yes | `production` | Execution mode (`development`, `production`, `testing`). |
| `APP_VERSION` | Backend / API | No | `1.0.0` | Semantic version string returned by `/version`. |
| `API_DEBUG` | Backend | No | `false` | When `true`, exposes raw tracebacks in error responses. Set `false` in production. |
| `DATABASE_HOST` | Backend / Scripts | Yes | — | PostgreSQL host address (RDS endpoint or `postgres` container). |
| `DATABASE_PORT` | Backend / Scripts | Yes | `5432` | PostgreSQL network port. |
| `DATABASE_NAME` | Backend / Scripts | Yes | `serving_db` | Serving relational database name. |
| `DATABASE_USER` | Backend / Scripts | Yes | `postgres` | Database authentication username. |
| `DATABASE_PASSWORD`| Backend / Scripts | Yes | — | Database authentication password. Never commit. |
| `DATABASE_SCHEMA` | Backend | No | `serving` | Schema containing analytical tables and views. |
| `CORS_ORIGINS` | Backend | Yes | `*` | Comma-separated list of allowed frontend origins in production. |
| `VITE_API_BASE_URL`| Frontend | Yes | `http://127.0.0.1:8000`| Base URL for API requests. In Nginx reverse-proxy setups, set to empty string or `/`. |
| `AWS_REGION` | Scripts / Glue | Yes | `ap-south-1` | Target AWS region. |
| `S3_BUCKET` | Ingestion / Glue | Yes | — | Target S3 bucket hosting Medallion data lakehouse. |

---

## 3. Containerized Production Deployment (Docker Compose)

The production configuration (`docker-compose.prod.yml`) provisions:
- An isolated PostgreSQL 16 Alpine container with persistent named volume.
- A hardened FastAPI container with health checks and restart policies.
- A multi-stage Nginx container serving precompiled React 19 static assets and reverse-proxying `/api` and `/health` requests with read-only root filesystems and temporary RAM mounts (`tmpfs`).

### 3.1 Step-by-Step Deployment

1. **Verify Prerequisites:**
   - Docker Engine $\ge 24.0$
   - Docker Compose $\ge 2.20$

2. **Configure Environment Secrets:**
   ```bash
   export POSTGRES_PASSWORD="your_secure_production_password"
   export DB_PASSWORD="$POSTGRES_PASSWORD"
   export CORS_ORIGINS="https://careerpulse.yourdomain.com"
   ```

3. **Build and Launch the Production Cluster:**
   ```bash
   docker compose -f docker-compose.prod.yml build
   docker compose -f docker-compose.prod.yml up -d
   ```

4. **Verify Container Health:**
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```
   *All containers (`cp-prod-postgres`, `cp-prod-backend`, `cp-prod-frontend`) must show `(healthy)` status.*

5. **Load Initial Gold Snapshot into PostgreSQL:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend python backend/load_gold_to_rds.py
   ```

---

## 4. Cloud-Native AWS Pipeline Deployment

To run the complete cloud pipeline on AWS:

### 4.1 Step 1: Deploy S3 Data Lake Buckets
Create your S3 bucket with three primary prefixes:
```bash
aws s3 mb s3://<YOUR_S3_BUCKET> --region ap-south-1
aws s3api put-bucket-versioning --bucket <YOUR_S3_BUCKET> --versioning-configuration Status=Suspended
```

### 4.2 Step 2: Deploy AWS Glue Crawlers & ETL Jobs
```bash
export S3_BUCKET="<YOUR_S3_BUCKET>"
export AWS_REGION="ap-south-1"

# 1. Deploy Bronze Crawler
python scripts/deploy_glue.py

# 2. Deploy Silver PySpark ETL Job
python scripts/deploy_glue_silver.py

# 3. Deploy Gold PySpark ETL Job
python scripts/deploy_glue_gold.py
```

### 4.3 Step 3: Provision Amazon RDS PostgreSQL
```bash
export DATABASE_PASSWORD="your_secure_rds_password"
python scripts/provision_rds.py
```
*The script automatically provisions a single-AZ `db.t4g.micro` PostgreSQL instance, authorizes your public IP on port 5432, and outputs connection instructions.*

### 4.4 Step 4: Execute Serving Layer Loader
```bash
export DATABASE_HOST="<YOUR_RDS_ENDPOINT>"
export DATABASE_PASSWORD="your_secure_rds_password"
python backend/load_gold_to_rds.py
```

---

## 5. Security & Maintenance Best Practices

1. **Security Group Ingress:** Never open PostgreSQL port 5432 to `0.0.0.0/0`. Restrict ingress strictly to the backend application server IP or ECS security group.
2. **Reverse Proxy TLS:** In public cloud deployments, terminate SSL/TLS at an AWS Application Load Balancer (ALB) or Cloudflare in front of the Nginx container on port 443.
3. **Log Rotation:** Docker container logs should use the `json-file` driver with `max-size: "10m"` and `max-file: "3"` to avoid disk exhaustion.
