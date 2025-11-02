"""Shared fixtures and mocks for pytest tests."""

import io
from datetime import UTC, datetime
from unittest.mock import Mock

import joblib
import numpy as np
import pandas as pd
import pytest
from google.cloud.storage import Blob


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Mock settings module for all tests."""
    # Mock at the settings module level - all imports will use these values
    monkeypatch.setattr("mlsys.settings.GCP_PROJECT_ID", "test-project")
    monkeypatch.setattr("mlsys.settings.GCS_BUCKET_MODELS_DEV", "mlsys-models-dev")
    monkeypatch.setattr("mlsys.settings.GCS_BUCKET_MODELS_STAGING", "mlsys-models-staging")
    monkeypatch.setattr("mlsys.settings.GCS_BUCKET_MODELS_PROD", "mlsys-models-prod")


@pytest.fixture
def sample_titanic_df():
    """Sample Titanic dataset for testing."""
    return pd.DataFrame(
        {
            "PassengerId": [1, 2, 3, 4, 5],
            "Pclass": [3, 1, 3, 1, 3],
            "Sex": [1, 0, 0, 0, 1],
            "Age": [22.0, 38.0, 26.0, 35.0, 35.0],
            "SibSp": [1, 1, 0, 1, 0],
            "Parch": [0, 0, 0, 0, 0],
            "Fare": [7.25, 71.28, 7.92, 53.1, 8.05],
            "Embarked": [0, 1, 0, 0, 0],
        }
    )


@pytest.fixture
def sample_predictions():
    """Sample prediction results."""
    return np.array([0, 1, 1, 1, 0])


@pytest.fixture
def sample_prediction_probabilities():
    """Sample prediction probabilities."""
    return np.array([0.3, 0.85, 0.75, 0.9, 0.4])


class MockSklearnModel:
    """Simple mock sklearn model for testing (can be pickled)."""

    def __init__(self, predictions, probabilities):
        self.predictions = predictions
        self.probabilities = probabilities

    def predict(self, X):  # noqa: ARG002
        return self.predictions

    def predict_proba(self, X):  # noqa: ARG002
        # Return 2D array with probabilities for each class
        return np.column_stack([1 - self.probabilities, self.probabilities])


@pytest.fixture
def mock_sklearn_model(sample_predictions, sample_prediction_probabilities):
    """Mock scikit-learn model."""
    return MockSklearnModel(sample_predictions, sample_prediction_probabilities)


@pytest.fixture
def mock_bq_client():
    """Mock BigQuery client."""
    client = Mock()
    client.project = "test-project"

    # Mock query job
    query_job = Mock()
    query_job.to_dataframe.return_value = pd.DataFrame(
        {"PassengerId": [1, 2, 3], "Pclass": [3, 1, 3]}
    )
    client.query.return_value = query_job

    # Mock load job
    load_job = Mock()
    load_job.result.return_value = None
    client.load_table_from_dataframe.return_value = load_job

    # Mock insert_rows_json for model registry
    client.insert_rows_json.return_value = []

    return client


@pytest.fixture
def mock_gcs_client():
    """Mock GCS client."""
    client = Mock()
    client.project = "test-project"

    # Mock bucket
    bucket = Mock()
    client.bucket.return_value = bucket

    # Mock blob for download/upload
    blob = Mock()
    blob.download_as_bytes.return_value = b"test content"
    blob.upload_from_string.return_value = None
    bucket.blob.return_value = blob

    return client


@pytest.fixture
def mock_gcs_blob():
    """Mock GCS blob object."""
    blob = Mock(spec=Blob)
    blob.name = "titanic-survival/v1/model.pkl"
    blob.size = 1024
    blob.time_created = datetime(2025, 1, 1, tzinfo=UTC)
    return blob


@pytest.fixture
def mock_gcs_blob_list():
    """Mock list of GCS blobs for model registry."""
    blobs = []

    # Valid model blob
    blob1 = Mock(spec=Blob)
    blob1.name = "titanic-survival/v1/model.pkl"
    blob1.size = 2048
    blob1.time_created = datetime(2025, 1, 1, tzinfo=UTC)
    blobs.append(blob1)

    # Another valid model blob
    blob2 = Mock(spec=Blob)
    blob2.name = "fraud-detection/v2/model.pkl"
    blob2.size = 4096
    blob2.time_created = datetime(2025, 1, 2, tzinfo=UTC)
    blobs.append(blob2)

    # Invalid blob - not a pickle file
    blob3 = Mock(spec=Blob)
    blob3.name = "titanic-survival/v1/metadata.json"
    blob3.size = 512
    blob3.time_created = datetime(2025, 1, 1, tzinfo=UTC)
    blobs.append(blob3)

    # Invalid blob - wrong path format
    blob4 = Mock(spec=Blob)
    blob4.name = "invalid/model.pkl"
    blob4.size = 1024
    blob4.time_created = datetime(2025, 1, 3, tzinfo=UTC)
    blobs.append(blob4)

    # Invalid blob - wrong version format
    blob5 = Mock(spec=Blob)
    blob5.name = "test-model/version1/model.pkl"
    blob5.size = 1024
    blob5.time_created = datetime(2025, 1, 4, tzinfo=UTC)
    blobs.append(blob5)

    return blobs


@pytest.fixture
def pickled_model_bytes(mock_sklearn_model):
    """Serialized model as bytes for GCS testing."""
    buffer = io.BytesIO()
    joblib.dump(mock_sklearn_model, buffer)
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def sample_metadata_json():
    """Sample metadata JSON for model registry."""
    return '{"description": "Titanic survival model", "accuracy": 0.85}'
