# Cloud Run Job for ML predictions
# This job runs the prediction pipeline from the Docker image
# Triggered by Cloud Scheduler jobs defined in cloud_scheduler.tf

resource "google_cloud_run_v2_job" "ml_predictions" {
  name                = "ml-predictions-${var.environment}"
  location            = var.region
  project             = var.project_id
  deletion_protection = false

  template {
    template {
      # Use the Docker image from Artifact Registry
      # Updated by CI/CD workflows (docker.yml)
      # Using placeholder image for initial Terraform apply
      containers {
        image = "gcr.io/cloudrun/hello"

        # Entry point: run the predict.py script
        # Arguments passed via Cloud Scheduler override these defaults
        args = [
          "python",
          "cloud_runs/predict.py",
          "--input_query=SELECT * FROM `${var.project_id}.sample_dataset.sample_table` LIMIT 10",
          "--output_table_id=${var.project_id}.predictions.sample_predictions",
          "--model_bucket=${var.bucket_models_name}",
          "--model_name=sample-model",
          "--model_version=v1"
        ]

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }

      # Maximum execution time (10 minutes)
      timeout = "600s"

      # Service account for the job
      # Needs permissions to read from BigQuery, read/write GCS, write to BigQuery
      service_account = google_service_account.predictions.email
    }
  }

  lifecycle {
    ignore_changes = [
      # Allow CI/CD to update the image without Terraform detecting drift
      template[0].template[0].containers[0].image,
    ]
  }
}

# Service account for prediction jobs
resource "google_service_account" "predictions" {
  account_id   = "run-ml-predictions-${var.environment}"
  project      = var.project_id
  display_name = "Cloud Run - ML Predictions (${var.environment})"
  description  = "Service account for Cloud Run Jobs that run ML prediction pipelines"
}

# Grant BigQuery Data Editor role (read/write tables)
resource "google_project_iam_member" "predictions_bq_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.predictions.email}"
}

# Grant BigQuery Job User role (run queries)
resource "google_project_iam_member" "predictions_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.predictions.email}"
}

# Grant Storage Object Viewer role (read model artifacts from GCS)
resource "google_project_iam_member" "predictions_gcs_object_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.predictions.email}"
}
