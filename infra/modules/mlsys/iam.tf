# IAM configuration for mlsys Cloud Run service
# Service accounts and permission bindings

# Service account for the Cloud Run service
resource "google_service_account" "mlsys" {
  account_id   = "mlsys-sa-${var.environment}"
  project      = var.project_id
  display_name = "Cloud Run - mlsys (${var.environment})"
  description  = "Service account for Cloud Run Service running predict and model_registry functions"
}

# Grant BigQuery Data Editor role (read/write tables)
resource "google_project_iam_member" "mlsys_bq_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.mlsys.email}"
}

# Grant BigQuery Job User role (run queries)
resource "google_project_iam_member" "mlsys_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.mlsys.email}"
}

# Grant Storage Object Admin role (full CRUD operations on GCS objects)
# Includes: read/download, list, create/write, delete, and update metadata
resource "google_project_iam_member" "mlsys_gcs_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.mlsys.email}"
}

# Allow unauthenticated invocations
# TODO: Add authentication later
resource "google_cloud_run_v2_service_iam_member" "mlsys_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.mlsys.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
