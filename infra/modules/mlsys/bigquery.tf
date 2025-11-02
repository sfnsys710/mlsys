# BigQuery dataset for ML system (training, predictions, model registry, etc.)
resource "google_bigquery_dataset" "mlsys" {
  dataset_id                 = "mlsys_${var.environment}"
  project                    = var.project_id
  location                   = var.region
  description                = "ML system dataset for training data, predictions, model registry, and related tables (${var.environment})"
  delete_contents_on_destroy = var.environment != "prod"
}

# Model registry table
resource "google_bigquery_table" "model_registry" {
  dataset_id          = google_bigquery_dataset.mlsys.dataset_id
  project             = var.project_id
  table_id            = "model_registry"
  deletion_protection = var.environment == "prod"

  schema = jsonencode([
    {
      name        = "model_name"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Name of the ML model"
    },
    {
      name        = "model_version"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Version number of the model"
    },
    {
      name        = "environment"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Environment where model is deployed (dev/staging/prod)"
    },
    {
      name        = "gcs_bucket"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "GCS bucket containing the model"
    },
    {
      name        = "file_size_bytes"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Size of the model file in bytes"
    },
    {
      name        = "upload_timestamp"
      type        = "TIMESTAMP"
      mode        = "NULLABLE"
      description = "When the model was uploaded to GCS"
    },
    {
      name        = "uploader"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "User or service account that uploaded the model"
    },
    {
      name        = "registered_at"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "When the model was registered in this table"
    },
    {
      name        = "metadata"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Optional JSON metadata for the model"
    }
  ])

  clustering = ["model_name", "environment", "model_version"]
}
