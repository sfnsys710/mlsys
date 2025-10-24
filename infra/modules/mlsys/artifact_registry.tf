# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "mlsys_images" {
  repository_id = var.artifact_registry_name
  project       = var.project_id
  location      = var.region
  description   = "Docker images for mlsys"
  format        = "DOCKER"
}
