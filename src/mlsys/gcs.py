"""GCS I/O utilities for uploading and downloading files and model artifacts."""

import io
from typing import Any

import joblib
from google.cloud import storage
from google.cloud.storage import Blob

from mlsys.settings import GCP_PROJECT_ID


def gcs_get(bucket_name: str, blob_path: str) -> bytes:
    """
    Download raw bytes from GCS.

    Args:
        bucket_name: GCS bucket name (e.g., "ml-models-dev")
        blob_path: Path to the blob within the bucket (e.g., "titanic-survival/v1/metadata.json")

    Returns:
        Raw bytes from the blob

    Example:
        >>> data = gcs_get("ml-models-dev", "titanic-survival/v1/metadata.json")
        >>> json_str = data.decode("utf-8")
    """
    client = storage.Client(project=GCP_PROJECT_ID)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    return blob.download_as_bytes()


def gcs_put(content: bytes | str, bucket_name: str, blob_path: str) -> None:
    """
    Upload raw bytes or string to GCS.

    Args:
        content: Content to upload (bytes or string)
        bucket_name: GCS bucket name (e.g., "ml-models-dev")
        blob_path: Path to the blob within the bucket (e.g., "titanic-survival/v1/metadata.json")

    Example:
        >>> import json
        >>> metadata = {"model": "titanic", "version": "v1"}
        >>> gcs_put(json.dumps(metadata), "ml-models-dev", "titanic-survival/v1/metadata.json")
    """
    client = storage.Client(project=GCP_PROJECT_ID)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Convert string to bytes if needed
    if isinstance(content, str):
        content = content.encode("utf-8")

    # Upload
    blob.upload_from_string(content)


def gcs_get_pickle(bucket_name: str, blob_path: str) -> Any:
    """
    Download and deserialize a pickled object from GCS.

    Args:
        bucket_name: GCS bucket name (e.g., "ml-models-dev")
        blob_path: Path to the blob within the bucket (e.g., "titanic-survival/v1/model.pkl")

    Returns:
        Deserialized object (typically a trained model)

    Example:
        >>> model = gcs_get_pickle("ml-models-dev", "titanic-survival/v1/model.pkl")
    """
    bytes_data = gcs_get(bucket_name, blob_path)
    return joblib.load(io.BytesIO(bytes_data))


def gcs_put_pickle(obj: Any, bucket_name: str, blob_path: str) -> None:
    """
    Serialize and upload an object to GCS using pickle/joblib.

    Args:
        obj: Object to upload (typically a trained model)
        bucket_name: GCS bucket name (e.g., "ml-models-dev")
        blob_path: Path to the blob within the bucket (e.g., "titanic-survival/v1/model.pkl")

    Example:
        >>> from sklearn.linear_model import LogisticRegression
        >>> model = LogisticRegression()
        >>> gcs_put_pickle(model, "ml-models-dev", "titanic-survival/v1/model.pkl")
    """
    # Serialize to bytes using joblib
    bytes_buffer = io.BytesIO()
    joblib.dump(obj, bytes_buffer)
    bytes_buffer.seek(0)

    # Upload using general gcs_put
    gcs_put(bytes_buffer.read(), bucket_name, blob_path)


def gcs_list_blobs(bucket_name: str) -> list[Blob]:
    """
    List all blobs in a GCS bucket.

    Args:
        bucket_name: GCS bucket name (e.g., "ml-models-dev")

    Returns:
        List of Blob objects with metadata (name, size, time_created, etc.)

    Example:
        >>> blobs = gcs_list_blobs("ml-models-dev")
        >>> for blob in blobs:
        ...     print(f"{blob.name} - {blob.size} bytes")
    """
    client = storage.Client(project=GCP_PROJECT_ID)
    bucket = client.bucket(bucket_name)

    # List all blobs in the bucket
    blobs = list(bucket.list_blobs())

    return blobs
