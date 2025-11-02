"""Unit tests for model registry script."""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from scripts.model_registry import model_registry


@pytest.mark.unit
class TestModelRegistry:
    """Test cases for model_registry function."""

    @patch("scripts.model_registry.bigquery.Client")
    @patch("scripts.model_registry.gcs_get")
    @patch("scripts.model_registry.gcs_list_blobs")
    def test_model_registry_success_dev(
        self,
        mock_list_blobs,
        mock_gcs_get,
        mock_bq_client_class,
        mock_gcs_blob_list,
        sample_metadata_json,
    ):
        """Test successful model registration in dev environment."""
        # Arrange
        mock_list_blobs.return_value = mock_gcs_blob_list
        mock_gcs_get.return_value = sample_metadata_json.encode("utf-8")

        mock_bq_client = Mock()
        mock_bq_client.insert_rows_json.return_value = []
        mock_bq_client_class.return_value = mock_bq_client

        env = "dev"

        # Act
        model_registry(env)

        # Assert
        # Verify blobs were listed
        mock_list_blobs.assert_called_once_with("mlsys-models-dev")

        # Verify BigQuery client was created
        mock_bq_client_class.assert_called_once()

        # Verify insert was called
        mock_bq_client.insert_rows_json.assert_called_once()
        call_args = mock_bq_client.insert_rows_json.call_args

        # Check table ID ends with correct dataset.table
        table_id = call_args[0][0]
        assert table_id.endswith(".mlsys_dev.model_registry")

        # Check rows to insert (only 2 valid .pkl files from fixture)
        rows = call_args[0][1]
        assert len(rows) == 2

        # Check first model (titanic-survival/v1/model.pkl)
        assert rows[0]["model_name"] == "titanic-survival"
        assert rows[0]["model_version"] == 1
        assert rows[0]["environment"] == "dev"
        assert rows[0]["gcs_bucket"] == "mlsys-models-dev"
        assert rows[0]["file_size_bytes"] == 2048

        # Check second model (fraud-detection/v2/model.pkl)
        assert rows[1]["model_name"] == "fraud-detection"
        assert rows[1]["model_version"] == 2

    @patch("scripts.model_registry.bigquery.Client")
    @patch("scripts.model_registry.gcs_get")
    @patch("scripts.model_registry.gcs_list_blobs")
    def test_model_registry_staging_environment(
        self,
        mock_list_blobs,
        mock_gcs_get,
        mock_bq_client_class,
        mock_gcs_blob_list,
    ):
        """Test model registration in staging environment."""
        # Arrange
        mock_list_blobs.return_value = mock_gcs_blob_list
        mock_gcs_get.side_effect = Exception("No metadata")

        mock_bq_client = Mock()
        mock_bq_client.insert_rows_json.return_value = []
        mock_bq_client_class.return_value = mock_bq_client

        env = "staging"

        # Act
        model_registry(env)

        # Assert
        mock_list_blobs.assert_called_once_with("mlsys-models-staging")
        call_args = mock_bq_client.insert_rows_json.call_args
        assert call_args[0][0].endswith(".mlsys_staging.model_registry")

    @patch("scripts.model_registry.bigquery.Client")
    @patch("scripts.model_registry.gcs_get")
    @patch("scripts.model_registry.gcs_list_blobs")
    def test_model_registry_prod_environment(
        self,
        mock_list_blobs,
        mock_gcs_get,
        mock_bq_client_class,
        mock_gcs_blob_list,
    ):
        """Test model registration in prod environment."""
        # Arrange
        mock_list_blobs.return_value = mock_gcs_blob_list
        mock_gcs_get.side_effect = Exception("No metadata")

        mock_bq_client = Mock()
        mock_bq_client.insert_rows_json.return_value = []
        mock_bq_client_class.return_value = mock_bq_client

        env = "prod"

        # Act
        model_registry(env)

        # Assert
        mock_list_blobs.assert_called_once_with("mlsys-models-prod")
        call_args = mock_bq_client.insert_rows_json.call_args
        assert call_args[0][0].endswith(".mlsys_prod.model_registry")

    @patch("scripts.model_registry.gcs_list_blobs")
    def test_model_registry_invalid_environment(self, mock_list_blobs):
        """Test that invalid environment raises ValueError."""
        # Arrange
        env = "invalid"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid environment"):
            model_registry(env)

        # Verify no GCS operations were performed
        mock_list_blobs.assert_not_called()

    @patch("scripts.model_registry.bigquery.Client")
    @patch("scripts.model_registry.gcs_get")
    @patch("scripts.model_registry.gcs_list_blobs")
    def test_model_registry_filters_non_pickle_files(
        self, mock_list_blobs, mock_gcs_get, mock_bq_client_class, mock_gcs_blob_list
    ):
        """Test that non-.pkl files are skipped."""
        # Arrange
        mock_list_blobs.return_value = mock_gcs_blob_list
        mock_gcs_get.side_effect = Exception("No metadata")

        mock_bq_client = Mock()
        mock_bq_client.insert_rows_json.return_value = []
        mock_bq_client_class.return_value = mock_bq_client

        # Act
        model_registry("dev")

        # Assert
        # Only 2 valid .pkl files should be registered
        # (metadata.json, invalid/model.pkl, test-model/version1/model.pkl are skipped)
        rows = mock_bq_client.insert_rows_json.call_args[0][1]
        assert len(rows) == 2
        assert all(row["model_name"] in ["titanic-survival", "fraud-detection"] for row in rows)

    @patch("scripts.model_registry.bigquery.Client")
    @patch("scripts.model_registry.gcs_get")
    @patch("scripts.model_registry.gcs_list_blobs")
    def test_model_registry_validates_version_format(
        self, mock_list_blobs, mock_gcs_get, mock_bq_client_class
    ):
        """Test that invalid version formats are skipped."""
        # Arrange
        # Create blob with invalid version format
        invalid_blob = Mock()
        invalid_blob.name = "model-name/version1/model.pkl"  # Should be v1, not version1
        invalid_blob.size = 1024
        invalid_blob.time_created = datetime(2025, 1, 1, tzinfo=UTC)

        mock_list_blobs.return_value = [invalid_blob]
        mock_gcs_get.side_effect = Exception("No metadata")

        mock_bq_client = Mock()
        mock_bq_client.insert_rows_json.return_value = []
        mock_bq_client_class.return_value = mock_bq_client

        # Act
        model_registry("dev")

        # Assert
        # No rows should be inserted (invalid version format)
        mock_bq_client.insert_rows_json.assert_not_called()

    @patch("scripts.model_registry.bigquery.Client")
    @patch("scripts.model_registry.gcs_get")
    @patch("scripts.model_registry.gcs_list_blobs")
    def test_model_registry_handles_missing_metadata(
        self, mock_list_blobs, mock_gcs_get, mock_bq_client_class, mock_gcs_blob_list
    ):
        """Test that models without metadata.json are still registered."""
        # Arrange
        mock_list_blobs.return_value = mock_gcs_blob_list
        # Simulate metadata file not found
        mock_gcs_get.side_effect = Exception("Blob not found")

        mock_bq_client = Mock()
        mock_bq_client.insert_rows_json.return_value = []
        mock_bq_client_class.return_value = mock_bq_client

        # Act
        model_registry("dev")

        # Assert
        # Models should still be registered with None metadata
        rows = mock_bq_client.insert_rows_json.call_args[0][1]
        assert len(rows) == 2
        # Metadata field should be None since gcs_get raised exception
        assert all(row.get("metadata") is None for row in rows)

    @patch("scripts.model_registry.bigquery.Client")
    @patch("scripts.model_registry.gcs_get")
    @patch("scripts.model_registry.gcs_list_blobs")
    def test_model_registry_with_metadata(
        self,
        mock_list_blobs,
        mock_gcs_get,
        mock_bq_client_class,
        mock_gcs_blob_list,
        sample_metadata_json,
    ):
        """Test that metadata.json is correctly loaded and included."""
        # Arrange
        mock_list_blobs.return_value = mock_gcs_blob_list
        mock_gcs_get.return_value = sample_metadata_json.encode("utf-8")

        mock_bq_client = Mock()
        mock_bq_client.insert_rows_json.return_value = []
        mock_bq_client_class.return_value = mock_bq_client

        # Act
        model_registry("dev")

        # Assert
        rows = mock_bq_client.insert_rows_json.call_args[0][1]
        # Both models should have metadata
        assert all(row["metadata"] == sample_metadata_json for row in rows)

    @patch("scripts.model_registry.bigquery.Client")
    @patch("scripts.model_registry.gcs_get")
    @patch("scripts.model_registry.gcs_list_blobs")
    def test_model_registry_empty_bucket(self, mock_list_blobs, mock_gcs_get, mock_bq_client_class):
        """Test that empty bucket doesn't attempt insert."""
        # Arrange
        mock_list_blobs.return_value = []

        mock_bq_client = Mock()
        mock_bq_client_class.return_value = mock_bq_client

        # Act
        model_registry("dev")

        # Assert
        # No insert should be attempted
        mock_bq_client.insert_rows_json.assert_not_called()

    @patch("scripts.model_registry.bigquery.Client")
    @patch("scripts.model_registry.gcs_get")
    @patch("scripts.model_registry.gcs_list_blobs")
    def test_model_registry_bigquery_error(
        self, mock_list_blobs, mock_gcs_get, mock_bq_client_class, mock_gcs_blob_list
    ):
        """Test that BigQuery insert errors are raised."""
        # Arrange
        mock_list_blobs.return_value = mock_gcs_blob_list
        mock_gcs_get.side_effect = Exception("No metadata")

        mock_bq_client = Mock()
        # Simulate BigQuery insert errors
        mock_bq_client.insert_rows_json.return_value = [{"error": "Insert failed"}]
        mock_bq_client_class.return_value = mock_bq_client

        # Act & Assert
        with pytest.raises(RuntimeError, match="BigQuery insert failed"):
            model_registry("dev")

    @patch("scripts.model_registry.bigquery.Client")
    @patch("scripts.model_registry.gcs_get")
    @patch("scripts.model_registry.gcs_list_blobs")
    def test_model_registry_row_structure(
        self, mock_list_blobs, mock_gcs_get, mock_bq_client_class, mock_gcs_blob_list
    ):
        """Test that registered rows have correct structure."""
        # Arrange
        mock_list_blobs.return_value = mock_gcs_blob_list[:1]  # Just first blob
        mock_gcs_get.side_effect = Exception("No metadata")

        mock_bq_client = Mock()
        mock_bq_client.insert_rows_json.return_value = []
        mock_bq_client_class.return_value = mock_bq_client

        # Act
        model_registry("dev")

        # Assert
        rows = mock_bq_client.insert_rows_json.call_args[0][1]
        row = rows[0]

        # Check all required fields are present
        assert "model_name" in row
        assert "model_version" in row
        assert "environment" in row
        assert "gcs_bucket" in row
        assert "file_size_bytes" in row
        assert "upload_timestamp" in row
        assert "uploader" in row
        assert "registered_at" in row
        assert "metadata" in row

        # Check uploader is marked as "scan"
        assert row["uploader"] == "scan"
