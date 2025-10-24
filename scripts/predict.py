"""Prediction script for Cloud Run jobs.

This script implements the core prediction pipeline:
1. Pull data from BigQuery
2. Pull model artifacts from GCS
3. Make predictions
4. Add metadata (timestamp, model name, model version)
5. Push predictions back to BigQuery

Usage:
    python scripts/predict.py \
        --input_query="SELECT * FROM project.dataset.input" \
        --output_table_id="project.dataset.predictions" \
        --model_bucket="ml-models-dev" \
        --model_name="titanic-survival" \
        --model_version="v1"
"""

import logging
from datetime import UTC, datetime

import fire

from mlsys.bq import bq_get, bq_put
from mlsys.gcs import gcs_get

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def pull_predict_push(
    input_query: str,
    output_table_id: str,
    model_bucket: str,
    model_name: str,
    model_version: str,
) -> None:
    """
    Pull data from BigQuery, make predictions, and push results back.

    Args:
        input_query: SQL query to fetch input data from BigQuery
        output_table_id: Fully qualified output table ID (e.g., "project.dataset.predictions")
        model_bucket: GCS bucket name containing the model (e.g., "ml-models-dev")
        model_name: Name of the model (e.g., "titanic-survival")
        model_version: Version of the model (e.g., "v1")
    """
    # Step 1: Pull data from BigQuery
    logger.info(f"Pulling data from BigQuery: {input_query[:100]}...")
    input_df = bq_get(input_query)
    logger.info(f"Fetched {len(input_df)} rows")

    # Step 2: Pull model artifacts from GCS
    # Construct blob path from naming convention: {model_name}/{model_version}/model.pkl
    model_blob_path = f"{model_name}/{model_version}/model.pkl"
    logger.info(f"Loading model from gs://{model_bucket}/{model_blob_path}")
    model = gcs_get(model_bucket, model_blob_path)
    logger.info(f"Model loaded: {type(model).__name__}")

    # Step 3: Make predictions
    logger.info("Making predictions...")
    predictions = model.predict(input_df)

    # Step 4: Add metadata
    logger.info("Adding metadata...")
    output_df = input_df.copy()
    output_df["prediction"] = predictions
    output_df["prediction_timestamp"] = datetime.now(UTC)
    output_df["model_name"] = model_name
    output_df["model_version"] = model_version

    # Step 5: Push predictions back to BigQuery
    logger.info(f"Pushing {len(output_df)} predictions to {output_table_id}")
    bq_put(output_df, output_table_id, write_disposition="WRITE_APPEND")
    logger.info("Predictions successfully written to BigQuery")


if __name__ == "__main__":
    fire.Fire(pull_predict_push)
