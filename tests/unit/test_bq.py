"""Unit tests for BigQuery I/O utilities."""

from unittest.mock import patch

import pandas as pd
import pytest

from mlsys.bq import bq_get, bq_put


@pytest.mark.unit
class TestBqGet:
    """Test cases for bq_get function."""

    @patch("mlsys.bq.bigquery.Client")
    def test_bq_get_success(self, mock_client_class, mock_bq_client):
        """Test successful query execution."""
        # Arrange
        mock_client_class.return_value = mock_bq_client
        query = "SELECT * FROM test_project.test_dataset.test_table"

        # Act
        result_df = bq_get(query)

        # Assert
        mock_client_class.assert_called_once()  # Don't check project ID - implementation detail
        mock_bq_client.query.assert_called_once_with(query)
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 3
        assert "PassengerId" in result_df.columns

    @patch("mlsys.bq.bigquery.Client")
    def test_bq_get_with_complex_query(self, mock_client_class, mock_bq_client):
        """Test query with WHERE clause and aggregations."""
        # Arrange
        mock_client_class.return_value = mock_bq_client
        query = """
            SELECT PassengerId, COUNT(*) as count
            FROM test_project.test_dataset.test_table
            WHERE Pclass = 1
            GROUP BY PassengerId
        """

        # Act
        result_df = bq_get(query)

        # Assert
        mock_bq_client.query.assert_called_once_with(query)
        assert isinstance(result_df, pd.DataFrame)

    @patch("mlsys.bq.bigquery.Client")
    def test_bq_get_empty_result(self, mock_client_class, mock_bq_client):
        """Test query that returns empty DataFrame."""
        # Arrange
        mock_client_class.return_value = mock_bq_client
        mock_bq_client.query.return_value.to_dataframe.return_value = pd.DataFrame()
        query = "SELECT * FROM test_project.test_dataset.empty_table"

        # Act
        result_df = bq_get(query)

        # Assert
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 0


@pytest.mark.unit
class TestBqPut:
    """Test cases for bq_put function."""

    @patch("mlsys.bq.bigquery.Client")
    def test_bq_put_with_write_append(self, mock_client_class, mock_bq_client):
        """Test uploading DataFrame with WRITE_APPEND disposition."""
        # Arrange
        mock_client_class.return_value = mock_bq_client
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        table_id = "test_project.test_dataset.test_table"

        # Act
        bq_put(df, table_id, write_disposition="WRITE_APPEND")

        # Assert
        mock_client_class.assert_called_once()
        mock_bq_client.load_table_from_dataframe.assert_called_once()

        # Check the arguments
        call_args = mock_bq_client.load_table_from_dataframe.call_args
        assert call_args[0][0].equals(df)  # DataFrame
        assert call_args[0][1] == table_id  # Table ID
        # The job_config is passed as a keyword argument
        job_config = call_args[1]["job_config"]
        assert job_config.write_disposition == "WRITE_APPEND"

    @patch("mlsys.bq.bigquery.Client")
    def test_bq_put_with_write_truncate(self, mock_client_class, mock_bq_client):
        """Test uploading DataFrame with WRITE_TRUNCATE disposition."""
        # Arrange
        mock_client_class.return_value = mock_bq_client
        df = pd.DataFrame({"col1": [1, 2], "col2": ["x", "y"]})
        table_id = "test_project.test_dataset.test_table"

        # Act
        bq_put(df, table_id, write_disposition="WRITE_TRUNCATE")

        # Assert
        call_args = mock_bq_client.load_table_from_dataframe.call_args
        # The job_config is passed as a keyword argument
        job_config = call_args[1]["job_config"]
        assert job_config.write_disposition == "WRITE_TRUNCATE"

    @patch("mlsys.bq.bigquery.Client")
    def test_bq_put_with_write_empty(self, mock_client_class, mock_bq_client):
        """Test uploading DataFrame with WRITE_EMPTY disposition."""
        # Arrange
        mock_client_class.return_value = mock_bq_client
        df = pd.DataFrame({"col1": [10], "col2": ["z"]})
        table_id = "test_project.test_dataset.test_table"

        # Act
        bq_put(df, table_id, write_disposition="WRITE_EMPTY")

        # Assert
        call_args = mock_bq_client.load_table_from_dataframe.call_args
        # The job_config is passed as a keyword argument
        job_config = call_args[1]["job_config"]
        assert job_config.write_disposition == "WRITE_EMPTY"

    @patch("mlsys.bq.bigquery.Client")
    def test_bq_put_default_write_disposition(self, mock_client_class, mock_bq_client):
        """Test that default write disposition is WRITE_APPEND."""
        # Arrange
        mock_client_class.return_value = mock_bq_client
        df = pd.DataFrame({"col1": [1], "col2": ["a"]})
        table_id = "test_project.test_dataset.test_table"

        # Act
        bq_put(df, table_id)  # No write_disposition specified

        # Assert
        call_args = mock_bq_client.load_table_from_dataframe.call_args
        # The job_config is passed as a keyword argument
        job_config = call_args[1]["job_config"]
        assert job_config.write_disposition == "WRITE_APPEND"

    @patch("mlsys.bq.bigquery.Client")
    def test_bq_put_waits_for_job_completion(self, mock_client_class, mock_bq_client):
        """Test that bq_put waits for the job to complete."""
        # Arrange
        mock_client_class.return_value = mock_bq_client
        df = pd.DataFrame({"col1": [1]})
        table_id = "test_project.test_dataset.test_table"

        # Act
        bq_put(df, table_id)

        # Assert
        mock_bq_client.load_table_from_dataframe.return_value.result.assert_called_once()
