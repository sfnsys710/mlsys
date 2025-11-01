# GCS buckets for mlsys

# Bucket for ML model artifacts
# Naming convention: mlsys-models-{environment}
resource "google_storage_bucket" "ml_models" {
  name                        = "mlsys-models-${var.environment}"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }
}
