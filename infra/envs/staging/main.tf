# Staging environment configuration

terraform {
  required_version = "~> 1.10.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Remote state in GCS
  # Initialize with: terraform init -backend-config="bucket=mlsys-terraform-state-staging"
  backend "gcs" {
    prefix = "mlsys/staging"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Call mlsys module with staging-specific variables
module "mlsys" {
  source = "../../modules/mlsys"

  project_id              = var.project_id
  region                  = var.region
  environment             = "staging"
  bucket_models_name      = "mlsys-models-staging"

  artifact_registry_name  = "mlsys-staging"
  bigquery_dataset_name   = "ml_registry_staging"
  model_registry_sa_name  = "model-registry-sa-staging"
}

# Variables
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

# Outputs
output "models_bucket_name" {
  value = module.mlsys.models_bucket_name
}

output "composer_bucket_name" {
  value = module.mlsys.composer_bucket_name
}

output "artifact_registry_name" {
  value = module.mlsys.artifact_registry_name
}

output "bigquery_dataset_id" {
  value = module.mlsys.bigquery_dataset_id
}

output "model_registry_sa_email" {
  value = module.mlsys.model_registry_sa_email
}
