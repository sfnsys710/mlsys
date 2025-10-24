"""Cloud Function for model registry.

This function is triggered when a new model artifact is uploaded to GCS buckets:
- ml-models-dev
- ml-models-staging
- ml-models-prod

It extracts metadata and registers the model in BigQuery (ml_registry.models table).
"""

import os
from datetime import UTC, datetime

from google.cloud import bigquery


def register_model(event: dict, _context: dict) -> None:
    """Register model metadata in BigQuery when a new model is uploaded to GCS.

    Args:
        event: Cloud Storage event data (dict with bucket, name, size, timeCreated, etc.)
        _context: Event context (dict with eventId, timestamp, eventType, resource) - unused

    Event structure:
        {
            "bucket": "ml-models-dev",
            "name": "titanic-survival/v1/model.pkl",
            "size": "12345",
            "timeCreated": "2024-01-15T10:30:00Z",
            "contentType": "application/octet-stream",
            "metageneration": "1",
            ...
        }
    """
    # Extract event data
    bucket_name = event["bucket"]
    blob_path = event["name"]
    file_size = int(event["size"])
    upload_timestamp = event["timeCreated"]

    # Determine environment from bucket name
    if bucket_name.endswith("-dev"):
        environment = "dev"
    elif bucket_name.endswith("-staging"):
        environment = "staging"
    elif bucket_name.endswith("-prod"):
        environment = "prod"
    else:
        print(f"Unknown bucket: {bucket_name}, skipping registration")
        return

    # Parse blob path to extract model name and version
    # Expected format: {model_name}/v{version}/{file_name}
    # Example: titanic-survival/v1/model.pkl
    parts = blob_path.split("/")
    if len(parts) < 3:
        print(
            f"Invalid blob path format: {blob_path}, "
            "expected {{model_name}}/v{{version}}/{{file}}"
        )
        return

    model_name = parts[0]
    version_str = parts[1]

    # Validate version format (v1, v2, etc.)
    if not version_str.startswith("v") or not version_str[1:].isdigit():
        print(f"Invalid version format: {version_str}, expected v{{N}}")
        return

    model_version = int(version_str[1:])  # Extract numeric version

    # Get uploader from event metadata (if available)
    uploader = event.get("metadata", {}).get("uploader", "unknown")

    # Prepare BigQuery row
    bq_project_id = os.getenv("GCP_PROJECT_ID", "soufianesys")
    dataset_id = "ml_registry"
    table_id = "models"
    full_table_id = f"{bq_project_id}.{dataset_id}.{table_id}"

    # Create BigQuery client
    client = bigquery.Client(project=bq_project_id)

    # Prepare row to insert
    row = {
        "model_name": model_name,
        "model_version": model_version,
        "environment": environment,
        "gcs_bucket": bucket_name,
        "gcs_path": blob_path,
        "file_size_bytes": file_size,
        "upload_timestamp": upload_timestamp,
        "uploader": uploader,
        "registered_at": datetime.now(UTC).isoformat(),
    }

    # Insert row into BigQuery
    errors = client.insert_rows_json(full_table_id, [row])

    if errors:
        print(f"Failed to register model: {errors}")
        raise RuntimeError(f"BigQuery insert failed: {errors}")

    print(
        f"Successfully registered model: {model_name} v{model_version} "
        f"in {environment} environment"
    )
