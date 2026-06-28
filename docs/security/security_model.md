# Security Model & IAM Architecture

## 1. Core Principles

- **Principle of Least Privilege (PoLP):** No resource or user is granted `AdministratorAccess`. Permissions are scoped strictly to the actions required for their specific function.

- **Role-Based Access Control (RBAC):** AWS services (for example, AWS Glue) assume IAM roles to interact with other services (for example, S3), rather than using hardcoded access keys.

## 2. IAM Users

### `careerpulse-admin` (Local Development)

- **Purpose:** Used via the AWS CLI on the local developer machine.
- **Permissions:** Scoped to manage S3, Glue, and RDS resources within the `cp-dev-*` naming convention.
- **Security:** MFA enabled; access keys rotated every 90 days.

## 3. IAM Roles & Trust Relationships

### `cp-dev-glue-role`

- **Assumed By:** `glue.amazonaws.com` (trust relationship)
- **Policies Attached:**
	- `AWSGlueServiceRole` (managed)
	- Custom inline policy: `cp-dev-s3-read-write` — restricts access only to the `cp-dev-datalake-*` bucket; no access to other S3 buckets in the account.
- **Rationale:** If the Glue job is compromised or misconfigured, it cannot delete or read data from unrelated projects in the AWS account.