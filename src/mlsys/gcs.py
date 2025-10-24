"""GCS I/O utilities for uploading and downloading model artifacts."""

import io
from typing import Any

import joblib
from google.cloud import storage

from mlsys.settings import GCP_PROJECT_ID


def gcs_get(bucket_name: str, blob_path: str) -> Any:
    """
    Download an object from GCS.

    Args:
        bucket_name: GCS bucket name (e.g., "ml-models-dev")
        blob_path: Path to the blob within the bucket (e.g., "titanic-survival/v1/model.pkl")

    Returns:
        Deserialized object (typically a trained model)

    Example:
        >>> model = gcs_get("ml-models-dev", "titanic-survival/v1/model.pkl")
    """
    client = storage.Client(project=GCP_PROJECT_ID)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Download to bytes
    bytes_data = blob.download_as_bytes()

    # Deserialize using joblib
    return joblib.load(io.BytesIO(bytes_data))


def gcs_put(obj: Any, bucket_name: str, blob_path: str) -> None:
    """
    Upload an object to GCS.

    Args:
        obj: Object to upload (typically a trained model)
        bucket_name: GCS bucket name (e.g., "ml-models-dev")
        blob_path: Path to the blob within the bucket (e.g., "titanic-survival/v1/model.pkl")

    Example:
        >>> from sklearn.linear_model import LogisticRegression
        >>> model = LogisticRegression()
        >>> gcs_put(model, "ml-models-dev", "titanic-survival/v1/model.pkl")
    """
    client = storage.Client(project=GCP_PROJECT_ID)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Serialize to bytes using joblib
    bytes_buffer = io.BytesIO()
    joblib.dump(obj, bytes_buffer)
    bytes_buffer.seek(0)

    # Upload
    blob.upload_from_file(bytes_buffer, content_type="application/octet-stream")
