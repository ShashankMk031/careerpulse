# Operational Metrics & Serving Layer Sizing Guide

To ensure optimal performance, observability, and debugging capabilities, CareerPulse records lightweight database synchronization metrics for every loader execution inside the `serving.load_metadata` table.

---

## 1. Description of Logged Metrics

The following metrics are collected in real-time by the load pipeline orchestrator:

* **`rows_per_second`** (float)
  * *Formula:* `records_loaded` / (`load_duration_ms` / 1000.0)
  * *Meaning:* Identifies overall pipeline throughput (including S3 download, validation, transformation, and database commit).
* **`bytes_processed`** (bigint)
  * *Meaning:* Combined size of S3 Gold Parquet objects read during the run, representing input volume scale.
* **`database_write_rate`** (float)
  * *Formula:* (`rows_inserted` + `rows_updated`) / (`transaction_duration_ms` / 1000.0)
  * *Meaning:* Measures PostgreSQL-specific insert and update throughput (excluding S3 file downloads and transformations).
* **`connection_wait_time_ms`** (float)
  * *Meaning:* Time spent by the thread waiting to acquire an active connection from the pool.
* **`transaction_duration_ms`** (float)
  * *Meaning:* Cumulative time elapsed executing database commands (TRUNCATE, INSERT ON CONFLICT) and committing the transaction.
* **`retry_count`** (int)
  * *Meaning:* Number of write retry attempts executed due to transient network drops or serialization failures.

---

## 2. Using Metrics to Identify Bottlenecks

### A. Connection Pool Exhaustion
* **Symptom:** High `connection_wait_time_ms` (e.g. > 5ms) on consecutive runs after pool warm-up.
* **Diagnosis:** If the API serving layer experiences high wait times, it means all connections in the pool (`maxconn`) are active and checked out.
* **Remedy:** Increase `DB_MAX_CONN` in the environment configurations, or verify that all database connection objects are properly returned back to the pool via the context manager (`finally: pool.putconn(conn)`).

### B. Database Write Latency & Locking
* **Symptom:** Low `database_write_rate` and high `transaction_duration_ms`.
* **Diagnosis:** PostgreSQL is slow writing rows. This is caused by CPU saturation, disk I/O bottlenecks, lock contention (two queries updating the same key), or heavy table check constraints.
* **Remedy:** Ensure the RDS instance class is adequately sized, verify GP3 IOPS storage configuration, or adjust batch pages sizes in `execute_values` (e.g. from 1,000 to 5,000).

### C. Network Transit Lag
* **Symptom:** High overall duration (`load_duration_ms`), but low database write duration (`transaction_duration_ms`).
* **Diagnosis:** S3 file downloads or network round trips between the loader host and the RDS server are taking most of the time.
* **Remedy:** Host the loader process inside the same AWS Region and subnet as the RDS instance (e.g. on EC2 or ECS) to reduce packet transit time to under 1ms.

---

## 3. Real-World Metrics Baseline (CareerPulse Sandbox Run)

Audit log output from a synchronized production polish run:

```text
Dataset      | Type    | Status  | Loaded | Rows/sec   | Bytes   | Write Rate | Conn Wait  | Tx Time   | Retries
--------------------------------------------------------------------------------------------------------------
summary      | REPLACE | SUCCESS | 1      | 1.77       | 4270    | 6.36       | 0.03       | 157.15    | 0      
technology   | UPSERT  | SUCCESS | 93     | 177.14     | 3118    | 956.98     | 0.02       | 97.18     | 0      
salary       | UPSERT  | SUCCESS | 1      | 2.35       | 1242    | 10.63      | 0.02       | 94.08     | 0      
geography    | UPSERT  | SUCCESS | 68     | 160.76     | 4034    | 761.33     | 0.02       | 89.32     | 0      
skills       | UPSERT  | SUCCESS | 93     | 189.80     | 2918    | 871.52     | 0.04       | 106.71    | 0      
company      | UPSERT  | SUCCESS | 85     | 56.89      | 6791    | 790.73     | 684.58     | 107.50    | 0      
```

### Metrics Observations:
* **Connection Pooling Validation:** The first dataset (`company`) experienced a `684.58 ms` connection wait because the ThreadedConnectionPool was cold, initializing TCP handshakes and starting backend PostgreSQL processes. All subsequent runs obtained connections in **`0.02 ms`** from the warm pool.
* **Write Rates:** The dynamic write rate ranges from `760` to `950` rows/second for UPSERTS, validating the efficiency of psycopg2 `execute_values`.
