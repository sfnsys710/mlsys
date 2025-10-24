# mlsys module main configuration

# Enable required GCP APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "storage.googleapis.com",          # Cloud Storage
    "bigquery.googleapis.com",         # BigQuery
    "run.googleapis.com",              # Cloud Run
    "cloudfunctions.googleapis.com",   # Cloud Functions
    "artifactregistry.googleapis.com", # Artifact Registry
    "iam.googleapis.com",              # IAM
    "composer.googleapis.com",         # Cloud Composer
  ])

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}
