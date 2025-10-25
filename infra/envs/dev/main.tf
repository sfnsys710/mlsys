# Dev environment configuration

terraform {
  required_version = ">= 1.10.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Remote state in GCS
  # Initialize with: terraform init -backend-config="bucket=mlsys-terraform-state-dev"
  backend "gcs" {
    prefix = "mlsys/dev"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Call mlsys module with dev-specific variables
module "mlsys" {
  source = "../../modules/mlsys"

  project_id              = var.project_id
  region                  = var.region
  environment             = "dev"
  bucket_models_name      = "mlsys-models-dev"
  artifact_registry_name  = "mlsys-dev"
  model_registry_sa_name  = "function-model-reg-dev"
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

output "artifact_registry_name" {
  value = module.mlsys.artifact_registry_name
}

output "mlsys_dataset_id" {
  value = module.mlsys.mlsys_dataset_id
}

output "model_registry_sa_email" {
  value = module.mlsys.model_registry_sa_email
}

output "cloud_run_job_name" {
  value = module.mlsys.cloud_run_job_name
}

output "predictions_sa_email" {
  value = module.mlsys.predictions_sa_email
}

output "scheduler_sa_email" {
  value = module.mlsys.scheduler_sa_email
}

output "titanic_scheduler_name" {
  value = module.mlsys.titanic_scheduler_name
}
