"""
Unit test suite for the CareerPulse ingestion pipeline components.
Covers utilities, schema validation, configuration, exceptions, uploader, S3 retry logic,
and the main orchestrator flow.
Targeting 25+ distinct test cases for robust production-grade verification.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import json
import hashlib

from ingestion.utils import get_utc_timestamp, generate_s3_key, generate_pipeline_id
from ingestion.exceptions import (
    PipelineStatus,
    ValidationError,
    RemoteOKEmptyResponseError,
    RemoteOKInvalidJSONError,
    RemoteOKTimeoutError,
    RemoteOKAPIError,
    S3BucketNotFoundError,
    S3CredentialsError,
    S3UploadFailedError,
    CareerPulseError,
)
from ingestion.schemas.remoteok import validate_remoteok_response
from ingestion.uploader import upload_json_to_s3
from ingestion.main import main, PipelineResult
import ingestion.config as config

# =====================================================================
# 1. UTILITIES TESTS
# =====================================================================

class TestIngestionUtils(unittest.TestCase):
    def test_get_utc_timestamp_timezone(self) -> None:
        ts = get_utc_timestamp()
        self.assertIsNotNone(ts.tzinfo)
        self.assertEqual(ts.tzinfo, timezone.utc)

    def test_generate_s3_key_jobs(self) -> None:
        dt = datetime(2026, 7, 10, 18, 46, 37, tzinfo=timezone.utc)
        jobs_key = generate_s3_key("remoteok", dt, "jobs")
        self.assertEqual(
            jobs_key,
            "bronze/source=remoteok/year=2026/month=07/day=10/jobs_20260710T184637Z.json"
        )

    def test_generate_s3_key_metadata(self) -> None:
        dt = datetime(2026, 7, 10, 18, 46, 37, tzinfo=timezone.utc)
        metadata_key = generate_s3_key("remoteok", dt, "metadata")
        self.assertEqual(
            metadata_key,
            "bronze/source=remoteok/year=2026/month=07/day=10/jobs_20260710T184637Z.metadata.json"
        )

    def test_generate_pipeline_id_format(self) -> None:
        dt = datetime(2026, 7, 10, 18, 46, 37, tzinfo=timezone.utc)
        pipeline_id = generate_pipeline_id(dt)
        self.assertTrue(pipeline_id.startswith("20260710T184637Z-"))
        self.assertEqual(len(pipeline_id), 16 + 1 + 6)  # timestamp + '-' + hex length

    def test_generate_pipeline_id_uniqueness(self) -> None:
        dt = datetime(2026, 7, 10, 18, 46, 37, tzinfo=timezone.utc)
        id1 = generate_pipeline_id(dt)
        id2 = generate_pipeline_id(dt)
        self.assertNotEqual(id1, id2)


# =====================================================================
# 2. STATUS ENUMS TESTS
# =====================================================================

class TestPipelineStatus(unittest.TestCase):
    def test_pipeline_status_values(self) -> None:
        self.assertEqual(PipelineStatus.SUCCESS.value, "SUCCESS")
        self.assertEqual(PipelineStatus.FAILED.value, "FAILED")
        self.assertEqual(PipelineStatus.PARTIAL_SUCCESS.value, "PARTIAL_SUCCESS")
        self.assertEqual(PipelineStatus.VALIDATION_FAILED.value, "VALIDATION_FAILED")
        self.assertEqual(PipelineStatus.UNKNOWN.value, "UNKNOWN")


# =====================================================================
# 3. CONFIGURATION TESTS
# =====================================================================

class TestIngestionConfig(unittest.TestCase):
    def test_config_pipeline_version(self) -> None:
        self.assertEqual(config.PIPELINE_VERSION, "0.1.0")

    def test_config_schema_version(self) -> None:
        self.assertEqual(config.SCHEMA_VERSION, 1)

    def test_config_source_name(self) -> None:
        self.assertEqual(config.SOURCE_NAME, "remoteok")

    def test_config_timeouts(self) -> None:
        self.assertTrue(config.REQUEST_TIMEOUT > 0)

    def test_config_s3_retries(self) -> None:
        self.assertTrue(config.S3_MAX_RETRIES >= 0)
        self.assertTrue(config.S3_BACKOFF_FACTOR > 0)
        self.assertIn("SlowDown", config.S3_TRANSIENT_ERRORS)


# =====================================================================
# 4. REMOTEOK VALIDATOR TESTS
# =====================================================================

class TestRemoteOKSchemaValidation(unittest.TestCase):
    def test_valid_payload(self) -> None:
        payload = [
            {"last_updated": 1234567, "legal": "some legal terms"},
            {"id": "123", "position": "Software Engineer", "company": "Acme Inc."},
            {"id": "124", "position": "Data Engineer", "company": "Global Corp."}
        ]
        # Should execute without throwing error
        validate_remoteok_response(payload)

    def test_invalid_top_level_dict(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_remoteok_response({"key": "value"})
        self.assertIn("expected a list", str(ctx.exception))

    def test_invalid_top_level_string(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_remoteok_response("hello")
        self.assertIn("expected a list", str(ctx.exception))

    def test_empty_payload(self) -> None:
        with self.assertRaises(RemoteOKEmptyResponseError) as ctx:
            validate_remoteok_response([])
        self.assertIn("response list is empty", str(ctx.exception))

    def test_invalid_metadata_type(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_remoteok_response(["not-a-dict"])
        self.assertIn("metadata) must be a dict", str(ctx.exception))

    def test_missing_metadata_fields(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_remoteok_response([
                {"legal": "some terms"},
                {"id": "123", "position": "Staff Engineer", "company": "Acme"}
            ])
        self.assertIn("missing the required 'last_updated' field", str(ctx.exception))

    def test_invalid_job_record_type(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_remoteok_response([
                {"last_updated": 12345},
                "not-a-dict"
            ])
        self.assertIn("expected a dict", str(ctx.exception))

    def test_missing_job_fields_id(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_remoteok_response([
                {"last_updated": 12345},
                {"position": "Staff Engineer", "company": "Acme"}
            ])
        self.assertIn("missing required fields: id", str(ctx.exception))

    def test_missing_job_fields_position(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_remoteok_response([
                {"last_updated": 12345},
                {"id": "123", "company": "Acme"}
            ])
        self.assertIn("missing required fields: position", str(ctx.exception))

    def test_missing_job_fields_company(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_remoteok_response([
                {"last_updated": 12345},
                {"id": "123", "position": "Software Engineer"}
            ])
        self.assertIn("missing required fields: company", str(ctx.exception))


# =====================================================================
# 5. S3 UPLOADER & RETRY LOGIC TESTS
# =====================================================================

class TestUploader(unittest.TestCase):
    @patch("ingestion.uploader.S3_BUCKET", None)
    def test_upload_s3_bucket_not_set(self) -> None:
        with self.assertRaises(S3UploadFailedError) as ctx:
            upload_json_to_s3({"key": "val"}, "test.json")
        self.assertIn("S3_BUCKET environment variable is not configured", str(ctx.exception))

    @patch("ingestion.uploader.S3_BUCKET", "mock-bucket")
    @patch("boto3.client")
    def test_upload_s3_success(self, mock_boto_client: MagicMock) -> None:
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.put_object.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200},
            "ETag": '"abc123etag"'
        }
        
        etag = upload_json_to_s3({"key": "value"}, "test_path.json")
        self.assertEqual(etag, "abc123etag")
        mock_s3.put_object.assert_called_once()

    @patch("ingestion.uploader.S3_BUCKET", "mock-bucket")
    @patch("boto3.client")
    def test_upload_s3_non_200_failure(self, mock_boto_client: MagicMock) -> None:
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.put_object.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 500}
        }
        
        with self.assertRaises(S3UploadFailedError) as ctx:
            upload_json_to_s3({"key": "value"}, "test_path.json")
        self.assertIn("non-200 status code", str(ctx.exception))

    @patch("ingestion.uploader.S3_BUCKET", "mock-bucket")
    @patch("boto3.client")
    def test_upload_s3_no_credentials_failure(self, mock_boto_client: MagicMock) -> None:
        from botocore.exceptions import NoCredentialsError
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.put_object.side_effect = NoCredentialsError()
        
        with self.assertRaises(S3CredentialsError) as ctx:
            upload_json_to_s3({"key": "value"}, "test_path.json")
        self.assertIn("AWS credentials not found", str(ctx.exception))

    @patch("ingestion.uploader.S3_BUCKET", "mock-bucket")
    @patch("boto3.client")
    def test_upload_s3_no_such_bucket_permanent_failure(self, mock_boto_client: MagicMock) -> None:
        from botocore.exceptions import ClientError
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.put_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Bucket does not exist"}},
            "PutObject"
        )
        
        with self.assertRaises(S3BucketNotFoundError) as ctx:
            upload_json_to_s3({"key": "value"}, "test_path.json")
        self.assertIn("S3 Bucket 'mock-bucket' not found", str(ctx.exception))

    @patch("ingestion.uploader.S3_BUCKET", "mock-bucket")
    @patch("boto3.client")
    def test_upload_s3_access_key_permanent_failure(self, mock_boto_client: MagicMock) -> None:
        from botocore.exceptions import ClientError
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.put_object.side_effect = ClientError(
            {"Error": {"Code": "InvalidAccessKeyId", "Message": "Access key is invalid"}},
            "PutObject"
        )
        
        with self.assertRaises(S3CredentialsError) as ctx:
            upload_json_to_s3({"key": "value"}, "test_path.json")
        self.assertIn("AWS credential validation failed", str(ctx.exception))

    @patch("ingestion.uploader.S3_BUCKET", "mock-bucket")
    @patch("ingestion.uploader.S3_MAX_RETRIES", 2)
    @patch("ingestion.uploader.S3_BACKOFF_FACTOR", 0.01)
    @patch("boto3.client")
    def test_upload_s3_transient_failure_retry_success(self, mock_boto_client: MagicMock) -> None:
        from botocore.exceptions import ClientError
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Throws SlowDown transient error on first attempt, then succeeds
        mock_s3.put_object.side_effect = [
            ClientError(
                {"Error": {"Code": "SlowDown", "Message": "Throttling"}},
                "PutObject"
            ),
            {
                "ResponseMetadata": {"HTTPStatusCode": 200},
                "ETag": '"success_etag"'
            }
        ]
        
        etag = upload_json_to_s3({"key": "value"}, "test_path.json")
        self.assertEqual(etag, "success_etag")
        self.assertEqual(mock_s3.put_object.call_count, 2)

    @patch("ingestion.uploader.S3_BUCKET", "mock-bucket")
    @patch("ingestion.uploader.S3_MAX_RETRIES", 2)
    @patch("ingestion.uploader.S3_BACKOFF_FACTOR", 0.01)
    @patch("boto3.client")
    def test_upload_s3_transient_failure_max_retries_reached(self, mock_boto_client: MagicMock) -> None:
        from botocore.exceptions import ClientError
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Throws RequestLimitExceeded on all 3 attempts
        mock_s3.put_object.side_effect = ClientError(
            {"Error": {"Code": "RequestLimitExceeded", "Message": "Throttling limit exceeded"}},
            "PutObject"
        )
        
        with self.assertRaises(S3UploadFailedError) as ctx:
            upload_json_to_s3({"key": "value"}, "test_path.json")
        self.assertIn("S3 upload failed with ClientError", str(ctx.exception))
        self.assertEqual(mock_s3.put_object.call_count, 3)

    @patch("ingestion.uploader.S3_BUCKET", "mock-bucket")
    @patch("ingestion.uploader.S3_MAX_RETRIES", 2)
    @patch("ingestion.uploader.S3_BACKOFF_FACTOR", 0.01)
    @patch("boto3.client")
    def test_upload_s3_unexpected_exception_retry_success(self, mock_boto_client: MagicMock) -> None:
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Throws a ConnectionError exception first, then succeeds
        mock_s3.put_object.side_effect = [
            ConnectionResetError("Connection reset by peer"),
            {
                "ResponseMetadata": {"HTTPStatusCode": 200},
                "ETag": '"success_etag_conn"'
            }
        ]
        
        etag = upload_json_to_s3({"key": "value"}, "test_path.json")
        self.assertEqual(etag, "success_etag_conn")
        self.assertEqual(mock_s3.put_object.call_count, 2)


# =====================================================================
# 6. MAIN ORCHESTRATOR TESTS
# =====================================================================

class TestMainOrchestrator(unittest.TestCase):
    @patch("ingestion.main.fetch_jobs")
    @patch("ingestion.main.upload_json_to_s3")
    def test_main_success_flow(self, mock_upload: MagicMock, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = {
            "metadata": {"last_updated": 123456},
            "jobs": [
                {"id": "1", "position": "Engineer", "company": "Acme"},
                {"id": "2", "position": "Analyst", "company": "Acme"}
            ]
        }
        mock_upload.return_value = "mock_etag"
        
        result = main()
        self.assertEqual(result.status, PipelineStatus.SUCCESS)
        self.assertEqual(result.records_processed, 2)
        self.assertEqual(result.records_uploaded, 2)
        self.assertIsNotNone(result.sha256)
        self.assertNil = result.error_message
        
        # Should calculate SHA-256 correctly
        jobs_json = json.dumps({"array": mock_fetch.return_value["jobs"]}, indent=2)
        expected_sha = hashlib.sha256(jobs_json.encode("utf-8")).hexdigest()
        self.assertEqual(result.sha256, expected_sha)
        
        # Verify both jobs and metadata upload were called
        self.assertEqual(mock_upload.call_count, 2)

    @patch("ingestion.main.fetch_jobs")
    def test_main_api_timeout_failure(self, mock_fetch: MagicMock) -> None:
        mock_fetch.side_effect = RemoteOKTimeoutError("Connection timed out")
        result = main()
        self.assertEqual(result.status, PipelineStatus.FAILED)
        self.assertIn("timed out", result.error_message)

    @patch("ingestion.main.fetch_jobs")
    def test_main_api_empty_response_failure(self, mock_fetch: MagicMock) -> None:
        mock_fetch.side_effect = RemoteOKEmptyResponseError("Empty payload")
        result = main()
        self.assertEqual(result.status, PipelineStatus.FAILED)
        self.assertIn("empty response", result.error_message)

    @patch("ingestion.main.fetch_jobs")
    def test_main_api_invalid_json_failure(self, mock_fetch: MagicMock) -> None:
        mock_fetch.side_effect = RemoteOKInvalidJSONError("Bad JSON format")
        result = main()
        self.assertEqual(result.status, PipelineStatus.FAILED)
        self.assertIn("invalid JSON", result.error_message)

    @patch("ingestion.main.fetch_jobs")
    def test_main_api_validation_failure(self, mock_fetch: MagicMock) -> None:
        mock_fetch.side_effect = ValidationError("Invalid keys")
        result = main()
        self.assertEqual(result.status, PipelineStatus.VALIDATION_FAILED)
        self.assertIn("validation failed", result.error_message)

    @patch("ingestion.main.fetch_jobs")
    @patch("ingestion.main.upload_json_to_s3")
    def test_main_s3_bucket_missing_failure(self, mock_upload: MagicMock, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = {
            "metadata": {"last_updated": 123},
            "jobs": [{"id": "1", "position": "Engineer", "company": "Acme"}]
        }
        mock_upload.side_effect = S3BucketNotFoundError("Bucket not found")
        
        result = main()
        self.assertEqual(result.status, PipelineStatus.FAILED)
        self.assertIn("Bucket configuration error", result.error_message)

    @patch("ingestion.main.fetch_jobs")
    @patch("ingestion.main.upload_json_to_s3")
    def test_main_s3_credentials_failure(self, mock_upload: MagicMock, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = {
            "metadata": {"last_updated": 123},
            "jobs": [{"id": "1", "position": "Engineer", "company": "Acme"}]
        }
        mock_upload.side_effect = S3CredentialsError("Creds missing")
        
        result = main()
        self.assertEqual(result.status, PipelineStatus.FAILED)
        self.assertIn("Credential resolution error", result.error_message)

    @patch("ingestion.main.fetch_jobs")
    @patch("ingestion.main.upload_json_to_s3")
    def test_main_s3_upload_failed_failure(self, mock_upload: MagicMock, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = {
            "metadata": {"last_updated": 123},
            "jobs": [{"id": "1", "position": "Engineer", "company": "Acme"}]
        }
        mock_upload.side_effect = S3UploadFailedError("Write error")
        
        result = main()
        self.assertEqual(result.status, PipelineStatus.FAILED)
        self.assertIn("S3 data upload failure", result.error_message)

    @patch("ingestion.main.fetch_jobs")
    def test_main_unexpected_exception_failure(self, mock_fetch: MagicMock) -> None:
        mock_fetch.side_effect = Exception("System crash")
        result = main()
        self.assertEqual(result.status, PipelineStatus.UNKNOWN)
        self.assertIn("Unexpected pipeline failure", result.error_message)
