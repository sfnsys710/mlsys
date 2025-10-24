# mlsys module outputs

output "models_bucket_name" {
  description = "GCS bucket name for ML models"
  value       = google_storage_bucket.ml_models.name
}

output "models_bucket_url" {
  description = "GCS bucket URL for ML models"
  value       = google_storage_bucket.ml_models.url
}

output "composer_bucket_name" {
  description = "GCS bucket name for Composer DAGs"
  value       = google_storage_bucket.composer_dags.name
}

output "composer_bucket_url" {
  description = "GCS bucket URL for Composer DAGs"
  value       = google_storage_bucket.composer_dags.url
}

output "artifact_registry_id" {
  description = "Artifact Registry repository ID"
  value       = google_artifact_registry_repository.mlsys_images.id
}

output "artifact_registry_name" {
  description = "Artifact Registry repository name"
  value       = google_artifact_registry_repository.mlsys_images.name
}

output "bigquery_dataset_id" {
  description = "BigQuery dataset ID for model registry"
  value       = google_bigquery_dataset.ml_registry.dataset_id
}

output "model_registry_sa_email" {
  description = "Model registry service account email"
  value       = google_service_account.model_registry.email
}

output "model_registry_table_id" {
  description = "BigQuery models table ID"
  value       = google_bigquery_table.models.table_id
}
