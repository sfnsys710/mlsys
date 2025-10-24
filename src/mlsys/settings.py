"""Configuration settings for mlsys."""

import os

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# GCP Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION")

# GCS Model Buckets
GCS_BUCKET_MODELS_DEV = os.getenv("GCS_BUCKET_MODELS_DEV", "ml-models-dev")
GCS_BUCKET_MODELS_STAGING = os.getenv("GCS_BUCKET_MODELS_STAGING", "ml-models-staging")
GCS_BUCKET_MODELS_PROD = os.getenv("GCS_BUCKET_MODELS_PROD", "ml-models-prod")

# Airflow Composer
COMPOSER_BUCKET_DEV = os.getenv("COMPOSER_BUCKET_DEV")
COMPOSER_BUCKET_STAGING = os.getenv("COMPOSER_BUCKET_STAGING")
COMPOSER_BUCKET_PROD = os.getenv("COMPOSER_BUCKET_PROD")
