# mlsys module outputs

output "models_bucket_name" {
  description = "GCS bucket name for ML models"
  value       = google_storage_bucket.ml_models.name
}

output "models_bucket_url" {
  description = "GCS bucket URL for ML models"
  value       = google_storage_bucket.ml_models.url
}

output "artifact_registry_id" {
  description = "Artifact Registry repository ID"
  value       = google_artifact_registry_repository.mlsys_images.id
}

output "artifact_registry_name" {
  description = "Artifact Registry repository name"
  value       = google_artifact_registry_repository.mlsys_images.name
}

output "mlsys_dataset_id" {
  description = "BigQuery dataset ID for ML system (training, predictions, model registry, etc.)"
  value       = google_bigquery_dataset.mlsys.dataset_id
}

output "model_registry_sa_email" {
  description = "Model registry service account email"
  value       = google_service_account.model_registry.email
}

output "model_registry_table_id" {
  description = "BigQuery model registry table ID"
  value       = google_bigquery_table.model_registry.table_id
}

output "cloud_run_job_name" {
  description = "Cloud Run Job name for predictions"
  value       = google_cloud_run_v2_job.ml_predictions.name
}

output "predictions_sa_email" {
  description = "Predictions service account email"
  value       = google_service_account.predictions.email
}

output "scheduler_sa_email" {
  description = "Cloud Scheduler service account email"
  value       = google_service_account.scheduler.email
}

output "titanic_scheduler_name" {
  description = "Titanic predictions Cloud Scheduler job name"
  value       = google_cloud_scheduler_job.titanic_predictions.name
}
