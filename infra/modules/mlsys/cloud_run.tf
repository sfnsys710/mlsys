# Cloud Run Service for ML predictions and model registry
# This service runs the FastAPI application from the Docker image
# Handles both /predict and /model-registry endpoints

resource "google_cloud_run_v2_service" "mlsys" {
  name                = "mlsys-${var.environment}"
  location            = var.region
  project             = var.project_id
  deletion_protection = false

  template {
    # Use the Docker image from Artifact Registry
    # Updated by CI/CD workflows (docker.yml)
    # Using placeholder image for initial Terraform apply
    containers {
      image = "gcr.io/cloudrun/hello"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      # Environment variables
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GCP_REGION"
        value = var.region
      }

      env {
        name  = "GCS_BUCKET_MODELS_DEV"
        value = "mlsys-models-dev"
      }

      env {
        name  = "GCS_BUCKET_MODELS_STAGING"
        value = "mlsys-models-staging"
      }

      env {
        name  = "GCS_BUCKET_MODELS_PROD"
        value = "mlsys-models-prod"
      }
    }

    # Maximum execution time (10 minutes)
    timeout = "600s"

    # Service account for the service
    # Needs permissions for both predict and model_registry functions:
    # - Read/write BigQuery tables
    # - Read/list GCS objects
    service_account = google_service_account.mlsys.email
  }

  lifecycle {
    ignore_changes = [
      # Allow CI/CD to update the image without Terraform detecting drift
      template[0].containers[0].image,
    ]
  }
}
