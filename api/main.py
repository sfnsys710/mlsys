"""FastAPI application for mlsys Cloud Run service.

This service provides HTTP endpoints for ML operations:
- /predict: Run predictions on data
- /register-model: Register model metadata
- /health: Health check endpoint
"""

import logging

from fastapi import FastAPI, HTTPException, Query

from scripts.model_registry import model_registry
from scripts.predict import predict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="mlsys",
    description="ML predictions and model registry for Cloud Run Service API",
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint - redirects to health check."""
    return {"status": "healthy"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy"}


@app.get("/predict")
async def predict_endpoint(
    env: str = Query(..., description="Environment (dev, staging, or prod)"),
    input_table: str = Query(
        ..., description='Fully qualified input table ID (e.g., "project.dataset.input")'
    ),
    output_table: str = Query(
        ..., description='Fully qualified output table ID (e.g., "project.dataset.predictions")'
    ),
    model_name: str = Query(..., description='Name of the model (e.g., "titanic-survival")'),
    model_version: str = Query(..., description='Version of the model (e.g., "v1")'),
) -> dict[str, str]:
    """
    Run predictions on data from BigQuery.

    This endpoint:
    1. Pulls data from BigQuery input table
    2. Loads the specified model from GCS (bucket determined by environment)
    3. Makes predictions
    4. Pushes results back to BigQuery output table with metadata

    Query Parameters:
    - env: Environment (dev/staging/prod) - determines which GCS bucket to use
    - input_table: Full BigQuery table path to read data from
    - output_table: Full BigQuery table path to write predictions to
    - model_name: Name of the model to use
    - model_version: Version of the model to use
    """
    try:
        logger.info(f"Received prediction request for {model_name} {model_version} in {env}")
        predict(
            env=env,
            input_table=input_table,
            output_table=output_table,
            model_name=model_name,
            model_version=model_version,
        )
        return {
            "status": "success",
            "message": f"Predictions completed for {model_name} {model_version}",
        }
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/model-registry")
async def model_registry_endpoint(
    env: str = Query(..., description="Environment (dev, staging, or prod)"),
) -> dict[str, str]:
    """
    Scan GCS bucket and register all model metadata in BigQuery.

    This endpoint lists all blobs in the specified environment's GCS bucket,
    extracts metadata for models following the naming convention
    {model_name}/v{version}/{file_name}, and upserts them to the BigQuery
    model_registry table.

    Query Parameters:
    - env: Environment (dev/staging/prod) - determines which GCS bucket to scan
    """
    try:
        logger.info(f"Received model registration request for {env} environment")
        model_registry(env=env)
        return {"status": "success", "message": f"Models registered for {env} environment"}
    except Exception as e:
        logger.error(f"Model registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
