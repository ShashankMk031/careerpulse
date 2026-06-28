# Data Dictionary : Bronze layer (Raw Ingestion) 

## 1. Operational Metadata  
* **Layer:** Bronze(Raw/ Immutable) 
* **Format:** Raw JSON (As recieved from source APIs) 
* **Write Frequency:** Daily batch (Triggered via AWS Glue Workflow) 
* **Primary Writer:** Python Ingestion scripts (Running on standard environment/Glue containers) 
* **Primary Reader:** AWS Glue Crawler & AWS Glue ETL Spark Jobs 
* **Retention Policy:** Indefinite (Historical snapshotting for bootstrapping and re-processing) 

## 2. Inbound Data Streams 
### Stream A : RemoteOK API 
* **Source Endpoint:** `https://remoteok.com/api`
* **Target S3 prefix:** `s3://cp-dev-datalake-321422008826/bronze/remoteok/year=YYYY/month=MM/day=DD/`
* **Core Fields Expected:** `id`, `epoch`, `company`, `position`, `tags`, `salary_min`, `salary_max`, `description`.

### Stream B : Adzuna API 
* **Source Endpoint:** `https://api.adzuna.com/v1/api/jobs/...`
* **Target S3 prefix:** `s3://cp-dev-datalake-321422008826/bronze/remoteok/year=YYYY/month=MM/day=DD/`
* **Core Fields Expected:** `id`, `title`, `description`, `salary_min`, `location`, `company`, `created`.