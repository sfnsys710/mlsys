"""Unit tests for prediction script."""

from datetime import UTC, datetime
from unittest.mock import patch

import pandas as pd
import pytest

from scripts.predict import predict


@pytest.mark.unit
class TestPredict:
    """Test cases for predict function."""

    @patch("scripts.predict.bq_put")
    @patch("scripts.predict.gcs_get_pickle")
    @patch("scripts.predict.bq_get")
    def test_predict_success_dev_environment(
        self,
        mock_bq_get,
        mock_gcs_get_pickle,
        mock_bq_put,
        sample_titanic_df,
        mock_sklearn_model,
    ):
        """Test successful prediction pipeline in dev environment."""
        # Arrange
        mock_bq_get.return_value = sample_titanic_df
        mock_gcs_get_pickle.return_value = mock_sklearn_model

        env = "dev"
        input_table = "test-project.titanic.test"
        output_table = "test-project.titanic.predictions"
        model_name = "titanic-survival"
        model_version = "v1"

        # Act
        predict(env, input_table, output_table, model_name, model_version)

        # Assert
        # Verify BigQuery query was called
        mock_bq_get.assert_called_once_with(f"SELECT * FROM {input_table}")

        # Verify model was loaded from correct bucket and path
        mock_gcs_get_pickle.assert_called_once_with(
            "mlsys-models-dev", "titanic-survival/v1/model.pkl"
        )

        # Verify output was written to BigQuery (predictions were made implicitly)
        mock_bq_put.assert_called_once()
        call_args = mock_bq_put.call_args

        # Check the output DataFrame structure
        output_df = call_args[0][0]
        assert isinstance(output_df, pd.DataFrame)
        assert len(output_df) == 5  # Same as input
        assert "PassengerId" in output_df.columns
        assert "Survived" in output_df.columns
        assert "PredictionProbability" in output_df.columns
        assert "PredictionTimestamp" in output_df.columns
        assert "ModelName" in output_df.columns
        assert "ModelVersion" in output_df.columns

        # Check metadata values
        assert (output_df["ModelName"] == model_name).all()
        assert (output_df["ModelVersion"] == model_version).all()

        # Check write disposition
        assert call_args[0][1] == output_table
        assert call_args[1]["write_disposition"] == "WRITE_APPEND"

    @patch("scripts.predict.bq_put")
    @patch("scripts.predict.gcs_get_pickle")
    @patch("scripts.predict.bq_get")
    def test_predict_success_staging_environment(
        self,
        mock_bq_get,
        mock_gcs_get_pickle,
        mock_bq_put,
        sample_titanic_df,
        mock_sklearn_model,
    ):
        """Test prediction pipeline in staging environment."""
        # Arrange
        mock_bq_get.return_value = sample_titanic_df
        mock_gcs_get_pickle.return_value = mock_sklearn_model

        env = "staging"
        input_table = "test-project.titanic.test"
        output_table = "test-project.titanic.predictions"
        model_name = "titanic-survival"
        model_version = "v2"

        # Act
        predict(env, input_table, output_table, model_name, model_version)

        # Assert
        mock_gcs_get_pickle.assert_called_once_with(
            "mlsys-models-staging", "titanic-survival/v2/model.pkl"
        )

    @patch("scripts.predict.bq_put")
    @patch("scripts.predict.gcs_get_pickle")
    @patch("scripts.predict.bq_get")
    def test_predict_success_prod_environment(
        self,
        mock_bq_get,
        mock_gcs_get_pickle,
        mock_bq_put,
        sample_titanic_df,
        mock_sklearn_model,
    ):
        """Test prediction pipeline in prod environment."""
        # Arrange
        mock_bq_get.return_value = sample_titanic_df
        mock_gcs_get_pickle.return_value = mock_sklearn_model

        env = "prod"
        input_table = "test-project.titanic.test"
        output_table = "test-project.titanic.predictions"
        model_name = "fraud-detection"
        model_version = "v3"

        # Act
        predict(env, input_table, output_table, model_name, model_version)

        # Assert
        mock_gcs_get_pickle.assert_called_once_with(
            "mlsys-models-prod", "fraud-detection/v3/model.pkl"
        )

    @patch("scripts.predict.bq_get")
    def test_predict_invalid_environment(self, mock_bq_get, sample_titanic_df):
        """Test that invalid environment raises ValueError."""
        # Arrange
        mock_bq_get.return_value = sample_titanic_df
        env = "invalid"
        input_table = "test-project.titanic.test"
        output_table = "test-project.titanic.predictions"
        model_name = "titanic-survival"
        model_version = "v1"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid environment"):
            predict(env, input_table, output_table, model_name, model_version)

    @patch("scripts.predict.bq_put")
    @patch("scripts.predict.gcs_get_pickle")
    @patch("scripts.predict.bq_get")
    def test_predict_with_different_model_versions(
        self,
        mock_bq_get,
        mock_gcs_get_pickle,
        mock_bq_put,
        sample_titanic_df,
        mock_sklearn_model,
    ):
        """Test prediction with different model versions."""
        # Arrange
        mock_bq_get.return_value = sample_titanic_df
        mock_gcs_get_pickle.return_value = mock_sklearn_model

        # Test v1
        predict("dev", "table.in", "table.out", "model-name", "v1")
        assert "model-name/v1/model.pkl" in mock_gcs_get_pickle.call_args[0][1]

        # Test v10
        predict("dev", "table.in", "table.out", "model-name", "v10")
        assert "model-name/v10/model.pkl" in mock_gcs_get_pickle.call_args[0][1]

    @patch("scripts.predict.bq_put")
    @patch("scripts.predict.gcs_get_pickle")
    @patch("scripts.predict.bq_get")
    def test_predict_output_dataframe_structure(
        self,
        mock_bq_get,
        mock_gcs_get_pickle,
        mock_bq_put,
        sample_titanic_df,
        mock_sklearn_model,
    ):
        """Test that output DataFrame has the correct structure and values."""
        # Arrange
        mock_bq_get.return_value = sample_titanic_df
        mock_gcs_get_pickle.return_value = mock_sklearn_model

        # Act
        predict("dev", "table.in", "table.out", "test-model", "v1")

        # Assert
        output_df = mock_bq_put.call_args[0][0]

        # Check columns
        expected_columns = [
            "PassengerId",
            "Survived",
            "PredictionProbability",
            "PredictionTimestamp",
            "ModelName",
            "ModelVersion",
        ]
        assert list(output_df.columns) == expected_columns

        # Check PassengerId matches input
        assert output_df["PassengerId"].tolist() == [1, 2, 3, 4, 5]

        # Check predictions (from mock)
        assert output_df["Survived"].tolist() == [0, 1, 1, 1, 0]

        # Check prediction probabilities
        assert len(output_df["PredictionProbability"]) == 5
        assert all(0 <= p <= 1 for p in output_df["PredictionProbability"])

        # Check timestamp is recent (within last minute)
        timestamps = output_df["PredictionTimestamp"]
        assert all(
            (datetime.now(UTC) - ts).total_seconds() < 60 for ts in timestamps if pd.notna(ts)
        )

        # Check metadata
        assert (output_df["ModelName"] == "test-model").all()
        assert (output_df["ModelVersion"] == "v1").all()
