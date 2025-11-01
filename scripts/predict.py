"""Prediction script for FastAPI service.

This script implements the core prediction pipeline:
1. Pull data from BigQuery
2. Pull model artifacts from GCS
3. Make predictions
4. Add metadata (timestamp, model name, model version)
5. Push predictions back to BigQuery
"""

import logging
from datetime import UTC, datetime

import fire

from mlsys.bq import bq_get, bq_put
from mlsys.gcs import gcs_get_pickle
from mlsys.settings import (
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


def predict(
    env: str,
    input_table: str,
    output_table: str,
    model_name: str,
    model_version: str,
) -> None:
    """
    Pull data from BigQuery, make predictions, and push results back.

    Args:
        env: Environment (dev, staging, or prod)
        input_table: Fully qualified input table ID (e.g., "project.dataset.input")
        output_table: Fully qualified output table ID (e.g., "project.dataset.predictions")
        model_name: Name of the model (e.g., "titanic-survival")
        model_version: Version of the model (e.g., "v1")
    """
    # Get model bucket based on environment
    bucket_map = {
        "dev": GCS_BUCKET_MODELS_DEV,
        "staging": GCS_BUCKET_MODELS_STAGING,
        "prod": GCS_BUCKET_MODELS_PROD,
    }
    model_bucket = bucket_map.get(env)
    if not model_bucket:
        raise ValueError(f"Invalid environment: {env}. Must be dev, staging, or prod")

    # Build query to fetch all data from input table
    input_query = f"SELECT * FROM {input_table}"
    # Step 1: Pull data from BigQuery
    logger.info(f"Pulling data from BigQuery: {input_query[:100]}...")
    input_df = bq_get(input_query)
    logger.info(f"Fetched {len(input_df)} rows")

    # Step 2: Pull model artifacts from GCS
    # Construct blob path from naming convention: {model_name}/{model_version}/model.pkl
    model_blob_path = f"{model_name}/{model_version}/model.pkl"
    logger.info(f"Loading model from gs://{model_bucket}/{model_blob_path}")
    model = gcs_get_pickle(model_bucket, model_blob_path)
    logger.info(f"Model loaded: {type(model).__name__}")

    # Step 3: Make predictions
    logger.info("Making predictions...")
    predictions = model.predict(input_df)
    prediction_probabilities = model.predict_proba(input_df)[:, 1]

    # Step 4: Create output dataframe with predictions and metadata
    logger.info("Adding metadata...")
    output_df = input_df[["PassengerId"]].copy()
    output_df["Survived"] = predictions
    output_df["PredictionProbability"] = prediction_probabilities
    output_df["PredictionTimestamp"] = datetime.now(UTC)
    output_df["ModelName"] = model_name
    output_df["ModelVersion"] = model_version

    # Step 5: Push predictions back to BigQuery
    logger.info(f"Pushing {len(output_df)} predictions to {output_table}")
    bq_put(output_df, output_table, write_disposition="WRITE_APPEND")
    logger.info("Predictions successfully written to BigQuery")


if __name__ == "__main__":
    fire.Fire(predict)
