# Cloud Scheduler jobs that trigger Cloud Run Jobs on a schedule
# Each model has its own scheduler job with specific parameters

# Example: Titanic Survival Predictions
# Runs daily at 2 AM UTC
resource "google_cloud_scheduler_job" "titanic_predictions" {
  name             = "titanic-predictions-${var.environment}"
  description      = "Daily titanic survival predictions (${var.environment})"
  schedule         = "0 2 * * *" # Every day at 2 AM UTC
  time_zone        = "UTC"
  region           = var.region
  project          = var.project_id
  attempt_deadline = "1800s" # 30 minutes max

  retry_config {
    retry_count = 3
    min_backoff_duration = "60s"
    max_backoff_duration = "300s"
  }

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.ml_predictions.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }

    # Override the default Cloud Run Job arguments with model-specific parameters
    body = base64encode(jsonencode({
      overrides = {
        containerOverrides = [{
          args = [
            "python",
            "cloud_runs/predict.py",
            "--input_query=SELECT * FROM `${var.project_id}.titanic_dataset.passenger_data` WHERE prediction_date = CURRENT_DATE()",
            "--output_table_id=${var.project_id}.predictions.titanic_survival",
            "--model_bucket=${var.bucket_models_name}",
            "--model_name=titanic-survival",
            "--model_version=v1"
          ]
        }]
      }
    }))
  }

  depends_on = [google_cloud_run_v2_job.ml_predictions]
}

# Service account for Cloud Scheduler
# Needs permission to invoke Cloud Run Jobs
resource "google_service_account" "scheduler" {
  account_id   = "cloud-scheduler-sa-${var.environment}"
  project      = var.project_id
  display_name = "Cloud Scheduler Service Account (${var.environment})"
  description  = "Service account for Cloud Scheduler to trigger Cloud Run Jobs"
}

# Grant Cloud Run Invoker role (trigger Cloud Run Jobs)
resource "google_project_iam_member" "scheduler_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scheduler.email}"
}

# Note: To add more scheduled predictions for other models,
# duplicate the google_cloud_scheduler_job resource above and modify:
# - name: e.g., "churn-predictions-${var.environment}"
# - description: e.g., "Weekly churn predictions"
# - schedule: e.g., "0 0 * * 0" for weekly on Sunday
# - body.overrides.containerOverrides[0].args: Update model parameters
