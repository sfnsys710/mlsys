"""Unit tests for GCS I/O utilities."""

import io
from unittest.mock import Mock, patch

import joblib
import pytest

from mlsys.gcs import gcs_get, gcs_get_pickle, gcs_list_blobs, gcs_put, gcs_put_pickle


@pytest.mark.unit
class TestGcsGet:
    """Test cases for gcs_get function."""

    @patch("mlsys.gcs.storage.Client")
    def test_gcs_get_success(self, mock_client_class, mock_gcs_client):
        """Test successful download of bytes from GCS."""
        # Arrange
        mock_client_class.return_value = mock_gcs_client
        bucket_name = "mlsys-models-dev"
        blob_path = "titanic-survival/v1/metadata.json"
        expected_content = b'{"accuracy": 0.85}'
        mock_gcs_client.bucket.return_value.blob.return_value.download_as_bytes.return_value = (
            expected_content
        )

        # Act
        result = gcs_get(bucket_name, blob_path)

        # Assert
        mock_client_class.assert_called_once()
        mock_gcs_client.bucket.assert_called_once_with(bucket_name)
        mock_gcs_client.bucket.return_value.blob.assert_called_once_with(blob_path)
        assert result == expected_content

    @patch("mlsys.gcs.storage.Client")
    def test_gcs_get_empty_file(self, mock_client_class, mock_gcs_client):
        """Test downloading an empty file."""
        # Arrange
        mock_client_class.return_value = mock_gcs_client
        bucket_name = "mlsys-models-dev"
        blob_path = "empty.txt"
        mock_gcs_client.bucket.return_value.blob.return_value.download_as_bytes.return_value = b""

        # Act
        result = gcs_get(bucket_name, blob_path)

        # Assert
        assert result == b""


@pytest.mark.unit
class TestGcsPut:
    """Test cases for gcs_put function."""

    @patch("mlsys.gcs.storage.Client")
    def test_gcs_put_with_bytes(self, mock_client_class, mock_gcs_client):
        """Test uploading bytes to GCS."""
        # Arrange
        mock_client_class.return_value = mock_gcs_client
        bucket_name = "mlsys-models-dev"
        blob_path = "test/file.txt"
        content = b"test content"

        # Act
        gcs_put(content, bucket_name, blob_path)

        # Assert
        mock_client_class.assert_called_once()
        mock_gcs_client.bucket.assert_called_once_with(bucket_name)
        mock_gcs_client.bucket.return_value.blob.assert_called_once_with(blob_path)
        mock_gcs_client.bucket.return_value.blob.return_value.upload_from_string.assert_called_once_with(  # noqa: E501
            content
        )

    @patch("mlsys.gcs.storage.Client")
    def test_gcs_put_with_string(self, mock_client_class, mock_gcs_client):
        """Test uploading string to GCS (should be converted to bytes)."""
        # Arrange
        mock_client_class.return_value = mock_gcs_client
        bucket_name = "mlsys-models-dev"
        blob_path = "test/metadata.json"
        content = '{"key": "value"}'

        # Act
        gcs_put(content, bucket_name, blob_path)

        # Assert
        # String should be converted to bytes
        expected_bytes = content.encode("utf-8")
        mock_gcs_client.bucket.return_value.blob.return_value.upload_from_string.assert_called_once_with(  # noqa: E501
            expected_bytes
        )

    @patch("mlsys.gcs.storage.Client")
    def test_gcs_put_empty_content(self, mock_client_class, mock_gcs_client):
        """Test uploading empty content."""
        # Arrange
        mock_client_class.return_value = mock_gcs_client
        bucket_name = "mlsys-models-dev"
        blob_path = "test/empty.txt"
        content = b""

        # Act
        gcs_put(content, bucket_name, blob_path)

        # Assert
        mock_gcs_client.bucket.return_value.blob.return_value.upload_from_string.assert_called_once_with(  # noqa: E501
            b""
        )


@pytest.mark.unit
class TestGcsGetPickle:
    """Test cases for gcs_get_pickle function."""

    @patch("mlsys.gcs.gcs_get")
    def test_gcs_get_pickle_success(self, mock_gcs_get, pickled_model_bytes, mock_sklearn_model):
        """Test successful download and deserialization of pickled object."""
        # Arrange
        mock_gcs_get.return_value = pickled_model_bytes
        bucket_name = "mlsys-models-dev"
        blob_path = "titanic-survival/v1/model.pkl"

        # Act
        result = gcs_get_pickle(bucket_name, blob_path)

        # Assert
        mock_gcs_get.assert_called_once_with(bucket_name, blob_path)
        assert hasattr(result, "predict")
        assert hasattr(result, "predict_proba")

    @patch("mlsys.gcs.gcs_get")
    def test_gcs_get_pickle_with_dict(self, mock_gcs_get):
        """Test deserializing a pickled dictionary."""
        # Arrange
        test_dict = {"model": "titanic", "version": "v1", "accuracy": 0.85}
        buffer = io.BytesIO()
        joblib.dump(test_dict, buffer)
        buffer.seek(0)
        mock_gcs_get.return_value = buffer.read()

        bucket_name = "mlsys-models-dev"
        blob_path = "config.pkl"

        # Act
        result = gcs_get_pickle(bucket_name, blob_path)

        # Assert
        assert isinstance(result, dict)
        assert result["model"] == "titanic"
        assert result["version"] == "v1"
        assert result["accuracy"] == 0.85


@pytest.mark.unit
class TestGcsPutPickle:
    """Test cases for gcs_put_pickle function."""

    @patch("mlsys.gcs.gcs_put")
    def test_gcs_put_pickle_with_model(self, mock_gcs_put, mock_sklearn_model):
        """Test serializing and uploading a model object."""
        # Arrange
        bucket_name = "mlsys-models-dev"
        blob_path = "titanic-survival/v1/model.pkl"

        # Act
        gcs_put_pickle(mock_sklearn_model, bucket_name, blob_path)

        # Assert
        mock_gcs_put.assert_called_once()
        call_args = mock_gcs_put.call_args[0]
        assert isinstance(call_args[0], bytes)  # First arg should be bytes
        assert call_args[1] == bucket_name
        assert call_args[2] == blob_path

        # Verify we can deserialize what was uploaded
        uploaded_bytes = call_args[0]
        deserialized_model = joblib.load(io.BytesIO(uploaded_bytes))
        assert hasattr(deserialized_model, "predict")

    @patch("mlsys.gcs.gcs_put")
    def test_gcs_put_pickle_with_dict(self, mock_gcs_put):
        """Test serializing and uploading a dictionary."""
        # Arrange
        test_dict = {"config": "value"}
        bucket_name = "mlsys-models-dev"
        blob_path = "config.pkl"

        # Act
        gcs_put_pickle(test_dict, bucket_name, blob_path)

        # Assert
        mock_gcs_put.assert_called_once()
        call_args = mock_gcs_put.call_args[0]
        assert isinstance(call_args[0], bytes)

        # Verify deserialization
        uploaded_bytes = call_args[0]
        deserialized_dict = joblib.load(io.BytesIO(uploaded_bytes))
        assert deserialized_dict == test_dict


@pytest.mark.unit
class TestGcsListBlobs:
    """Test cases for gcs_list_blobs function."""

    @patch("mlsys.gcs.storage.Client")
    def test_gcs_list_blobs_success(self, mock_client_class, mock_gcs_blob_list):
        """Test listing all blobs in a bucket."""
        # Arrange
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_bucket = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.list_blobs.return_value = mock_gcs_blob_list

        bucket_name = "mlsys-models-dev"

        # Act
        result = gcs_list_blobs(bucket_name)

        # Assert
        mock_client_class.assert_called_once()
        mock_client.bucket.assert_called_once_with(bucket_name)
        mock_bucket.list_blobs.assert_called_once()
        assert len(result) == 5  # Should have all blobs from fixture
        assert result[0].name == "titanic-survival/v1/model.pkl"

    @patch("mlsys.gcs.storage.Client")
    def test_gcs_list_blobs_empty_bucket(self, mock_client_class):
        """Test listing blobs in an empty bucket."""
        # Arrange
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_bucket = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.list_blobs.return_value = []

        bucket_name = "mlsys-models-dev"

        # Act
        result = gcs_list_blobs(bucket_name)

        # Assert
        assert len(result) == 0
        assert isinstance(result, list)
