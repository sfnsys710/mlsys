# mlsys module variables

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, or prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "bucket_models_name" {
  description = "GCS bucket name for ML model artifacts"
  type        = string
}

variable "bucket_composer_name" {
  description = "GCS bucket name for Airflow Composer DAGs"
  type        = string
}

variable "artifact_registry_name" {
  description = "Artifact Registry repository name for Docker images"
  type        = string
}

variable "bigquery_dataset_name" {
  description = "BigQuery dataset name for model registry"
  type        = string
}

variable "model_registry_sa_name" {
  description = "Service account name for model registry Cloud Function"
  type        = string
}
