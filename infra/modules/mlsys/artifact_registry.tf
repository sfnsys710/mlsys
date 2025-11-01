# Artifact Registry for Docker images
# Naming convention: mlsys-{environment}
resource "google_artifact_registry_repository" "mlsys_images" {
  repository_id = "mlsys-${var.environment}"
  project       = var.project_id
  location      = var.region
  description   = "Docker images for mlsys (${var.environment})"
  format        = "DOCKER"
}
