# AWS Infrastructure Cost & Budget Optimization Guide

## 1. Executive Summary

CareerPulse was architected specifically for cloud efficiency and developer budget predictability. By combining serverless data transformations (AWS Glue with minimum DPU limits) with right-sized serving resources (`db.t4g.micro` Amazon RDS), the platform keeps operational costs negligible while processing production data.

> [!CAUTION]
> **Cost Notice:** While the platform minimizes resource utilization, running infrastructure on AWS is **not inherently $0**. Charges depend on active runtime, data transfer, and AWS account tier limits. Always inspect the AWS Billing & Cost Management Dashboard and configure AWS Budget alerts.

---

## 2. Service Cost Breakdown & Budget Controls

| Service | Tier / Size | Pricing Metric | Cost-Control Mechanism Implemented |
| :--- | :--- | :--- | :--- |
| **AWS Glue (ETL)** | Spark 3.3 (2 DPUs) | \$0.44 per DPU-Hour (\$0.88/hr) | Strict **10-minute job timeout** (`Timeout=10`) + allocated exactly **2 DPUs** (`NumberOfWorkers=2`). |
| **AWS Glue (Crawler)** | Serverless Crawler | \$0.44 per DPU-Hour | Scheduled on-demand only; crawlers never run in continuous polling loops. |
| **Amazon RDS** | `db.t4g.micro` (PostgreSQL) | ~\$0.018/hour (~\$13/month) | **Single-AZ deployment**, general purpose gp3 storage (20 GB), and **manual stop when idle**. |
| **Amazon S3** | Standard Storage | \$0.023 per GB-Month | Versioning disabled for temporary artifacts; Parquet columnar compression reduces storage by ~85%. |
| **AWS Athena** | Serverless SQL | \$5.00 per TB scanned | Partition pruning on date keys; query result cleanup at `s3://.../athena-results/`. |
| **AWS IAM / VPC** | Managed Networking | \$0.00 | Free native security groups and IAM roles. |

---

## 3. Critical Cost-Control Strategies

### 3.1 AWS Glue Execution Guardrails
AWS Glue bills in 1-second increments with a 1-minute minimum per execution. Without guardrails, hanging Spark jobs can rapidly consume AWS credits.
- **Enforced 10-Minute Timeout:** Both `cp_dev_silver_etl` and `cp_dev_gold_etl` enforce a strict `Timeout=10` parameter in their job definitions. If an unexpected deadlock occurs, AWS automatically terminates the worker nodes after 10 minutes.
- **Minimum 2-DPU Allocation:** Standard Glue jobs default to 10 DPUs ($4.40/hr). CareerPulse explicitly pins `NumberOfWorkers=2` (`WorkerType="G.1X"`), cutting hourly runtime costs by 80%.
- **Incremental Bookmarks:** Glue job bookmarks prevent reprocessing historical raw data, ensuring ETL execution times stay between 45–90 seconds per run.

### 3.2 Amazon RDS Lifecycle Management
The PostgreSQL database runs on an ARM-based Graviton2 `db.t4g.micro` instance (2 vCPUs, 1 GB RAM). While AWS Free Tier includes 750 hours/month of `db.t4g.micro` for 12 months on eligible accounts:
- **Stop When Not In Use:** Stop the RDS instance when not actively developing:
  ```bash
  aws rds stop-db-instance --db-instance-identifier cp-dev-serving-db --region ap-south-1
  ```
  *(Note: Amazon RDS automatically restarts stopped instances after 7 days to apply maintenance; keep this in mind when planning extended offline periods).*
- **Start On-Demand:**
  ```bash
  aws rds start-db-instance --db-instance-identifier cp-dev-serving-db --region ap-south-1
  ```

### 3.3 S3 Storage & Athena Optimization
- **Snappy Parquet Compression:** Ingested JSON (~500 KB per scrape) is compressed into Snappy Parquet in Silver and Gold, reducing stored footprint to under 50 KB.
- **Athena Result Expiration:** Athena query outputs written to `s3://<S3_BUCKET>/athena-results/` should be purged periodically via an S3 Lifecycle Rule configured to delete objects older than 3 days.

---

## 4. Cost-Control Pre-Flight Checklist

Before launching ingestion runs or deploying infrastructure, verify:
- [ ] AWS Budget alert is set (e.g., alert at $5.00/month threshold).
- [ ] Glue ETL jobs specify `Timeout=10` and `NumberOfWorkers=2`.
- [ ] Amazon RDS instance is `db.t4g.micro` and `MultiAZ=False`.
- [ ] S3 bucket versioning is suspended unless explicitly required.
- [ ] Local testing uses Docker Compose (`docker compose up -d`) rather than live AWS compute whenever possible.
