# Service account for model registry Cloud Function
resource "google_service_account" "model_registry" {
  account_id   = var.model_registry_sa_name
  project      = var.project_id
  display_name = "Cloud Function - Model Registry (${var.environment})"
  description  = "Service account for Cloud Function that registers models in BigQuery when uploaded to GCS"
}

# Grant BigQuery Data Editor role (allows inserting data)
resource "google_project_iam_member" "model_registry_bq_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.model_registry.email}"
}

# Grant BigQuery Job User role (allows running queries/inserts)
resource "google_project_iam_member" "model_registry_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.model_registry.email}"
}
