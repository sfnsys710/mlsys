"""BigQuery I/O utilities for reading and writing data."""

import pandas as pd
from google.cloud import bigquery

from mlsys.settings import GCP_PROJECT_ID


def bq_get(query: str) -> pd.DataFrame:
    """
    Execute a BigQuery query and return results as a DataFrame.

    Args:
        query: SQL query string. Table paths should be fully qualified
               (e.g., "SELECT * FROM project.dataset.table")

    Returns:
        pandas DataFrame with query results

    Example:
        >>> df = bq_get("SELECT * FROM myproject.mydataset.mytable LIMIT 10")
    """
    client = bigquery.Client(project=GCP_PROJECT_ID)
    query_job = client.query(query)
    return query_job.to_dataframe()


def bq_put(
    df: pd.DataFrame,
    table_id: str,
    write_disposition: str = "WRITE_APPEND",
) -> None:
    """
    Upload a DataFrame to BigQuery.

    Args:
        df: pandas DataFrame to upload
        table_id: Fully qualified table ID (e.g., "project.dataset.table")
        write_disposition: How to handle existing data:
            - "WRITE_APPEND": Append to existing table (default)
            - "WRITE_TRUNCATE": Replace existing table
            - "WRITE_EMPTY": Only write if table is empty

    Example:
        >>> df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        >>> bq_put(df, "myproject.mydataset.mytable", "WRITE_TRUNCATE")
    """
    client = bigquery.Client(project=GCP_PROJECT_ID)

    job_config = bigquery.LoadJobConfig(write_disposition=write_disposition)

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for the job to complete
