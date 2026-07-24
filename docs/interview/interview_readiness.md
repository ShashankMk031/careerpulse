# Interview Readiness & Cost Optimization Review

This document prepares you for technical interviews by detailing the architectural trade-offs, security designs, scalability designs, and cost models implemented in **CareerPulse**.

---

## 1. Architectural Decisions & Trade-Offs

### Decision A: Consolidated Gold Orchestrator vs. Six Separate Glue Jobs
* **Context:** In early sprints, separate Glue jobs were proposed for Company, Skills, Geography, Salary, Technology, and Summary tables.
* **Trade-off:**
  * *Separate Jobs:* High modularity. If one aggregation logic changes, only that job runs. However, AWS Glue has a minimum startup overhead billing period (1 minute). Running 6 separate jobs incurs 6x startup overhead costs.
  * *Consolidated Job (Orchestrator Pattern):* We run a single Glue ETL job (`cp_dev_gold_etl`) that reads Silver once and writes all 6 datasets.
* **Verdict:** We chose the **Consolidated Orchestrator** pattern because, at current scale, it saves up to 80% on compute cost by sharing the Spark Context initialization and avoiding multiple startup billing overheads. It can be easily split into separate jobs using Glue Workflow triggers if scale demands it later.

### Decision B: Dynamic Schema-Drift Protection vs. Static Schemas
* **Context:** Third-party APIs (RemoteOK, Adzuna) change their JSON structures without notice (e.g. dropping columns or changing field names).
* **Trade-off:**
  * *Static Schemas:* Spark job fails immediately upon missing columns (`AnalysisException`), causing pipeline breakdown.
  * *Dynamic Schema-Drift Protection:* In `validate_schema()`, we extract actual field names from the Glue Catalog using `df.schema["array"].dataType.elementType.fieldNames()`. If a field is missing, we select `lit(None).cast(DataType)` instead of failing.
* **Verdict:** We chose **Dynamic Schema-Drift Protection** to build a robust, self-healing pipeline that tolerates API updates and logs warnings instead of crashing.

---

## 2. Security & Compliance Design

* **Least Privilege IAM Roles:** The AWS Glue Job executes under a dedicated role (`cp-dev-glue-role`) configured with strict policies restricted to the project S3 buckets (`cp-dev-datalake-321422008826`) and specific Glue Catalog tables. No admin permissions.
* **Data-at-Rest Encryption:** All data on S3 is encrypted using server-side encryption with Amazon S3 managed keys (SSE-S3).
* **Data-in-Transit Encryption:** All API calls use SSL (HTTPS) and AWS requests are signed using Signature Version 4.

---

## 3. Cost Optimization Matrix (DPU & Worker Scalability)

AWS Glue compute is billed per Data Processing Unit (DPU) hour ($0.44/DPU-hour). We analyze three scaling scenarios to optimize DPU configurations:

| Scenario / Scale | Active Postings | Ingestion / Glue Frequency | DPU Configuration | Expected Monthly Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Low Scale** | ~100 / day | Once Daily | 2 DPUs (Standard Workers) | **~$1.50 / month** |
| **Medium Scale** | ~10,000 / day | Hourly Batching | 2-4 DPUs (G.1X Workers) | **~$15 - $25 / month** |
| **High Scale** | ~100,000 / day | Continuous (Micro-batch) | 5-10 DPUs with Auto Scaling | **~$150 - $220 / month** |

### Key Cost Optimization Strategies Implemented:
1. **Glue Job Bookmarks:** By enabling bookmarks, we prevent reprocessing of historical partitions, keeping processing times flat even as data scales.
2. **Columnar Parquet & Snappy Compression:** Storing Silver and Gold layers in Parquet format with Snappy compression reduces data scan volume in Athena by up to 90%, minimizing Athena costs ($5.00 per TB scanned).
3. **Partition Pruning:** Athena queries query specific subfolders using partition columns (`year`, `month`, `day`), skipping scan reads for unneeded data.

---

## 4. Key Scalability Concepts to Explain in Interviews

1. **Broadcast Join Optimization:**
   In `generate_skills_analytics`, the overall average salary is computed as a single driver scalar (`overall_avg_max_salary`) and broadcasted via `lit()` to all nodes. This avoids expensive shuffle operations across the Spark cluster.
2. **Window Function Partitioning:**
   Deduplication in the Silver layer is executed using `row_number().over(Window.partitionBy("id").orderBy(desc("epoch")))`. This distributes rows by job ID, ensuring memory is optimized per partition key.
3. **Struct-Based Maximum Extraction:**
   To extract the highest paying role per company in SQL/Spark without running separate subqueries, we aggregate using:
   `coalesce(max(struct("salary_max", "position"))["position"], "Unknown")`
   This is a highly optimized Spark pattern that packages the sorting key and target value into a struct, enabling maximum-based extraction in a single linear pass.
