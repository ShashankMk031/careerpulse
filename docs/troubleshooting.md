# CareerPulse Troubleshooting Guide

## 1. Overview

This troubleshooting runbook provides diagnostics and immediate remediation procedures for common operational issues encountered across local development, AWS data pipelines, backend APIs, and the frontend dashboard.

---

## 2. Database Connectivity Issues

### 2.1 Issue: `psycopg2.OperationalError: could not connect to server: Connection timed out`
- **Root Cause:** Your local developer public IPv4 address has changed, and the RDS Security Group (`cp-dev-rds-sg`) ingress rule is rejecting connections on port 5432.
- **Diagnostic:**
  ```bash
  # Check your current public IP
  curl -s https://api.ipify.org
  ```
- **Remediation:**
  1. Determine your current public IP:
     ```bash
     CURRENT_IP=$(curl -s https://api.ipify.org)
     echo "Current IP: $CURRENT_IP"
     ```
  2. Authorize ONLY your current IP in the RDS Security Group:
     ```bash
     SG_ID=$(aws ec2 describe-security-groups --group-names cp-dev-rds-sg --query 'SecurityGroups[0].GroupId' --output text --region ap-south-1)
     aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 5432 --cidr ${CURRENT_IP}/32 --region ap-south-1
     ```
  3. Verify connection:
     ```bash
     source venv/bin/activate && python -c "from backend.database.pool import initialize_pool; initialize_pool()"
     ```

### 2.2 Issue: Port Collision (`5432` vs `5433`)
- **Root Cause:** A local PostgreSQL service running on your host machine occupies port 5432 while Docker Compose attempts to bind port 5433 or vice versa.
- **Diagnostic:**
  ```bash
  lsof -i :5432
  lsof -i :5433
  ```
- **Remediation:**
  - In `docker-compose.yml`, the local PostgreSQL container maps `5433:5432` to avoid host port collisions.
  - When connecting to local Docker PostgreSQL, ensure `DATABASE_PORT=5433`.
  - When connecting to AWS RDS PostgreSQL, ensure `DATABASE_PORT=5432`.

---

## 3. AWS Glue Data Pipeline Issues

### 3.1 Issue: Glue Job Fails with `AccessDeniedException`
- **Root Cause:** The IAM role (`cp-dev-glue-role`) lacks permissions to read from the S3 Bronze bucket or write to S3 Silver/Gold.
- **Diagnostic:** Check AWS CloudWatch Logs at `/aws-glue/jobs/error`.
- **Remediation:** Verify that `cp-dev-glue-role` has:
  1. `AWSGlueServiceRole` managed policy attached.
  2. S3 inline policy granting `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject`, and `s3:ListBucket` on `arn:aws:s3:::<S3_BUCKET>` and `arn:aws:s3:::<S3_BUCKET>/*`.

### 3.2 Issue: Glue Job Processes Zero Records (Bookmark Issue)
- **Root Cause:** Glue Job Bookmarks are enabled, and Glue believes the Bronze partition was already processed by a previous run.
- **Remediation:**
  - Reset the job bookmark via AWS CLI:
    ```bash
    aws glue reset-job-bookmark --job-name cp_dev_silver_etl --region ap-south-1
    ```
  - Or trigger the job with bookmarks disabled for backfilling:
    ```bash
    aws glue start-job-run --job-name cp_dev_silver_etl --arguments '{"--job-bookmark-option": "job-bookmark-disable"}' --region ap-south-1
    ```

---

## 4. FastAPI Backend Issues

### 4.1 Issue: `CRITICAL: Serving database host config 'DATABASE_HOST' is missing or blank`
- **Root Cause:** The application started without configuring the database host in `.env`.
- **Remediation:**
  1. Ensure `.env` exists in the root directory or `backend/.env`.
  2. Verify that `DATABASE_HOST` (or `DB_HOST`) is defined and points to your valid RDS endpoint or `localhost`.

### 4.2 Issue: CORS Blocked in Browser (`Cross-Origin Request Blocked`)
- **Root Cause:** The frontend origin is not in `CORS_ORIGINS`.
- **Remediation:**
  In `.env`, update `CORS_ORIGINS` to include the frontend address:
  ```env
  CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost
  ```
  Restart the FastAPI server.

---

## 5. React Frontend Issues

### 5.1 Issue: Network Error / API Requests Fail in Dashboard
- **Root Cause:** `VITE_API_BASE_URL` is pointing to an unreachable host or port.
- **Diagnostic:** Inspect Browser DevTools $\rightarrow$ Network tab for failed requests to `/api/v1/...`.
- **Remediation:**
  1. Check `frontend/.env` has:
     ```env
     VITE_API_BASE_URL=http://127.0.0.1:8000
     ```
  2. Confirm FastAPI is running and responds to `curl http://127.0.0.1:8000/health`.
  3. Rebuild the frontend dev server (`npm --prefix frontend run dev`).

### 5.2 Issue: TypeScript or Build Fails on Subpath Imports
- **Root Cause:** Stale node modules or TypeScript compilation caches.
- **Remediation:**
  ```bash
  cd frontend
  rm -rf node_modules/.vite dist
  npm run build
  ```
