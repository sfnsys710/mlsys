# GCS buckets for mlsys

# Bucket for ML model artifacts
resource "google_storage_bucket" "ml_models" {
  name                        = var.bucket_models_name
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }
}

# Bucket for Airflow Composer DAGs
resource "google_storage_bucket" "composer_dags" {
  name                        = var.bucket_composer_name
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }
}
