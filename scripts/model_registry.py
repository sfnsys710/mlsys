"""Model registry script for FastAPI service.

This script scans all models in a GCS bucket and registers/updates them in BigQuery.
It lists all blobs in the bucket, extracts metadata, and upserts to the model_registry table.
"""

import logging
from datetime import UTC, datetime

import fire
from google.cloud import bigquery

from mlsys.gcs import gcs_get, gcs_list_blobs
from mlsys.settings import (
    GCP_PROJECT_ID,
    GCS_BUCKET_MODELS_DEV,
    GCS_BUCKET_MODELS_PROD,
    GCS_BUCKET_MODELS_STAGING,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def model_registry(env: str) -> None:
    """Scan GCS bucket and register all model metadata in BigQuery.

    This function lists all blobs in the specified environment's GCS bucket,
    extracts metadata for models following the naming convention
    {model_name}/v{version}/{file_name}, and upserts them to the BigQuery
    model_registry table.

    Args:
        env: Environment (dev, staging, or prod)
    """
    # Get bucket name based on environment
    bucket_map = {
        "dev": GCS_BUCKET_MODELS_DEV,
        "staging": GCS_BUCKET_MODELS_STAGING,
        "prod": GCS_BUCKET_MODELS_PROD,
    }
    bucket_name = bucket_map.get(env)
    if not bucket_name:
        raise ValueError(f"Invalid environment: {env}. Must be dev, staging, or prod")

    logger.info(f"Scanning bucket {bucket_name} for models...")

    # List all blobs in the bucket
    blobs = gcs_list_blobs(bucket_name)
    logger.info(f"Found {len(blobs)} blobs in bucket")

    # Prepare BigQuery table reference
    dataset_id = f"mlsys_{env}"
    table_id = "model_registry"
    full_table_id = f"{GCP_PROJECT_ID}.{dataset_id}.{table_id}"

    # Create BigQuery client
    bq_client = bigquery.Client(project=GCP_PROJECT_ID)

    # Prepare rows to upsert
    rows_to_upsert = []
    registered_count = 0
    skipped_count = 0

    for blob in blobs:
        blob_path = blob.name

        # Only process pickle files (model.pkl)
        if not blob_path.endswith(".pkl"):
            logger.debug(f"Skipping {blob_path}: not a pickle file")
            skipped_count += 1
            continue

        # Parse blob path to extract model name and version
        # Expected format: {model_name}/v{version}/{file_name}
        # Example: titanic-survival/v1/model.pkl
        parts = blob_path.split("/")
        if len(parts) < 3:
            logger.debug(
                f"Skipping {blob_path}: invalid path format, "
                "expected {{model_name}}/v{{version}}/{{file}}"
            )
            skipped_count += 1
            continue

        model_name = parts[0]
        version_str = parts[1]

        # Validate version format (v1, v2, etc.)
        if not version_str.startswith("v") or not version_str[1:].isdigit():
            logger.debug(f"Skipping {blob_path}: invalid version format {version_str}")
            skipped_count += 1
            continue

        model_version = int(version_str[1:])  # Extract numeric version

        # Try to read metadata.json from the same directory
        metadata_path = f"{model_name}/{version_str}/metadata.json"
        metadata_content = None
        try:
            metadata_bytes = gcs_get(bucket_name, metadata_path)
            metadata_content = metadata_bytes.decode("utf-8")
            logger.debug(f"Found metadata for {blob_path}")
        except Exception as e:
            logger.debug(f"No metadata found at {metadata_path}: {e}")

        # Prepare row to upsert
        row = {
            "model_name": model_name,
            "model_version": model_version,
            "environment": env,
            "gcs_bucket": bucket_name,
            "file_size_bytes": blob.size,
            "upload_timestamp": blob.time_created.isoformat(),
            "uploader": "scan",  # Mark as scanned since we don't have uploader metadata
            "registered_at": datetime.now(UTC).isoformat(),
            "metadata": metadata_content,
        }
        rows_to_upsert.append(row)
        registered_count += 1

    if not rows_to_upsert:
        logger.info("No models found to register")
        return

    # Insert rows into BigQuery
    logger.info(f"Upserting {len(rows_to_upsert)} models to {full_table_id}")
    errors = bq_client.insert_rows_json(full_table_id, rows_to_upsert)

    if errors:
        logger.error(f"Failed to register models: {errors}")
        raise RuntimeError(f"BigQuery insert failed: {errors}")

    logger.info(
        f"Successfully registered {registered_count} models in {env} environment "
        f"(skipped {skipped_count} non-model blobs)"
    )


if __name__ == "__main__":
    fire.Fire(model_registry)
