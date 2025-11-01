# Staging environment configuration

terraform {
  required_version = ">= 1.10.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Remote state in GCS
  backend "gcs" {
    bucket = "mlsys-terraform-state-staging"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Call mlsys module with staging-specific variables
module "mlsys" {
  source = "../../modules/mlsys"

  project_id  = var.project_id
  region      = var.region
  environment = "staging"
}

# Variables
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

# Outputs
output "models_bucket_name" {
  value = module.mlsys.models_bucket_name
}

output "artifact_registry_name" {
  value = module.mlsys.artifact_registry_name
}

output "mlsys_dataset_id" {
  value = module.mlsys.mlsys_dataset_id
}

output "cloud_run_service_name" {
  value = module.mlsys.cloud_run_service_name
}

output "mlsys_sa_email" {
  value = module.mlsys.mlsys_sa_email
}
