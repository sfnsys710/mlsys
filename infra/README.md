# Infrastructure - Terraform

Modular Terraform configuration for managing GCP infrastructure across dev, staging, and prod environments.

## Overview

**Terraform Version**: 1.10.0 (managed via `.terraform-version`)

**Architecture**: Reusable module pattern with environment-specific deployments

**Environments**: dev, staging, prod (same GCP project, separate resources)

## Directory Structure

```
infra/
├── .terraform-version           # Terraform version constraint (1.10.0)
├── terraform.tfvars.example     # Example variables template
├── README.md                    # This file
├── envs/                        # Environment-specific configurations
│   ├── dev/
│   │   └── main.tf             # Dev environment (calls mlsys module)
│   ├── staging/
│   │   └── main.tf             # Staging environment (calls mlsys module)
│   └── prod/
│       └── main.tf             # Production environment (calls mlsys module)
└── modules/
    └── mlsys/                   # Core mlsys infrastructure module
        ├── main.tf              # Required APIs + local variables
        ├── variables.tf         # Module input variables
        ├── outputs.tf           # Module outputs
        ├── gcs_buckets.tf       # GCS buckets (models + composer)
        ├── bigquery.tf          # BigQuery dataset and model registry table
        ├── artifact_registry.tf # Docker image repository
        └── service_accounts.tf  # Service accounts with IAM roles
```

## Base Infrastructure (mlsys Module)

The `mlsys` module creates the following resources per environment:

### GCS Buckets (2 per environment)
- **`mlsys-models-{env}`** - ML model artifacts
  - Versioning enabled
  - Lifecycle: Delete archived versions after 90 days
  - Uniform bucket-level access
- **`mlsys-composer-{env}`** - Airflow Composer DAGs
  - Versioning enabled
  - Uniform bucket-level access

### Artifact Registry
- **`mlsys-{env}`** - Docker image repository
  - Format: DOCKER
  - For Cloud Run job images

### BigQuery
- **Dataset**: `ml_registry_{env}` - Model registry dataset
- **Table**: `models` - Model metadata tracking
  - Partitioned by `registered_at` (daily)
  - Clustered by `model_name`, `environment`, `model_version`
  - Schema: model name, version, environment, GCS path, file size, timestamps, uploader

### Service Account
- **`model-registry-sa-{env}@{project}.iam.gserviceaccount.com`**
  - For model registry Cloud Function
  - IAM roles: `roles/bigquery.dataEditor`, `roles/bigquery.jobUser`

### Enabled APIs
- Cloud Storage, BigQuery, Cloud Run, Cloud Functions, Artifact Registry, IAM, Composer

## Prerequisites

### 1. Install Terraform

Version 1.10.0 required:

```bash
# Using tfenv (recommended)
tfenv install 1.10.0
tfenv use 1.10.0

# Or download from https://www.terraform.io/downloads
```

### 2. GCP Authentication

```bash
gcloud auth application-default login
gcloud config set project soufianesys
```

### 3. Create State Buckets (One-Time Setup)

Manual creation required for remote state management:

```bash
# Dev state bucket
gcloud storage buckets create gs://mlsys-terraform-state-dev \
  --project=soufianesys \
  --location=us-central1 \
  --uniform-bucket-level-access

gcloud storage buckets update gs://mlsys-terraform-state-dev \
  --versioning

# Staging state bucket
gcloud storage buckets create gs://mlsys-terraform-state-staging \
  --project=soufianesys \
  --location=us-central1 \
  --uniform-bucket-level-access

gcloud storage buckets update gs://mlsys-terraform-state-staging \
  --versioning

# Prod state bucket
gcloud storage buckets create gs://mlsys-terraform-state-prod \
  --project=soufianesys \
  --location=us-central1 \
  --uniform-bucket-level-access

gcloud storage buckets update gs://mlsys-terraform-state-prod \
  --versioning
```

## Local Development Workflow

### Dev Environment

```bash
# Navigate to dev environment
cd infra/envs/dev

# Initialize Terraform with dev state bucket
terraform init -backend-config="bucket=mlsys-terraform-state-dev"

# Create terraform.tfvars (optional for local dev)
cp ../../terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Validate configuration
terraform fmt
terraform validate

# Plan changes
terraform plan -var="project_id=soufianesys" -var="region=us-central1"

# Apply changes
terraform apply -var="project_id=soufianesys" -var="region=us-central1"
```

### Staging Environment

```bash
cd infra/envs/staging

terraform init -backend-config="bucket=mlsys-terraform-state-staging"
terraform plan -var="project_id=soufianesys" -var="region=us-central1"
terraform apply -var="project_id=soufianesys" -var="region=us-central1"
```

### Production Environment

```bash
cd infra/envs/prod

terraform init -backend-config="bucket=mlsys-terraform-state-prod"
terraform plan -var="project_id=soufianesys" -var="region=us-central1"
terraform apply -var="project_id=soufianesys" -var="region=us-central1"
```

## CI/CD Workflow

GitHub Actions will use command-line variables instead of terraform.tfvars:

```bash
# Example: Dev deployment
cd infra/envs/dev
terraform init -backend-config="bucket=mlsys-terraform-state-dev"
terraform plan \
  -var="project_id=${GCP_PROJECT_ID}" \
  -var="region=${GCP_REGION}"
terraform apply -auto-approve \
  -var="project_id=${GCP_PROJECT_ID}" \
  -var="region=${GCP_REGION}"
```

## State Management

**Backend**: GCS with separate buckets per environment
- Dev: `gs://mlsys-terraform-state-dev/mlsys/dev/`
- Staging: `gs://mlsys-terraform-state-staging/mlsys/staging/`
- Prod: `gs://mlsys-terraform-state-prod/mlsys/prod/`

**Features**:
- Versioning enabled for state rollback
- State locking via GCS (automatic)
- Complete environment isolation

## Adding Model-Specific Resources

Users will add model-specific infrastructure by creating new Terraform files in each environment:

### Example: Adding titanic-survival Model Resources

Create `infra/envs/dev/titanic_survival.tf`:

```hcl
# Service account for titanic-survival DAG
resource "google_service_account" "titanic_survival_dag" {
  account_id   = "titanic-survival-dag-sa-dev"
  project      = var.project_id
  display_name = "Titanic Survival DAG (dev)"
}

# Grant permissions to read models from GCS
resource "google_storage_bucket_iam_member" "titanic_dag_models_reader" {
  bucket = module.mlsys.models_bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.titanic_survival_dag.email}"
}

# Grant permissions to write predictions to BigQuery
resource "google_project_iam_member" "titanic_dag_bq_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.titanic_survival_dag.email}"
}

# Cloud Run job (optional - can be created via gcloud or console)
resource "google_cloud_run_v2_job" "titanic_prediction" {
  name     = "titanic-survival-prediction-dev"
  location = var.region
  project  = var.project_id

  template {
    template {
      service_account = google_service_account.titanic_survival_dag.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${module.mlsys.artifact_registry_name}/titanic-survival:latest"

        env {
          name  = "MODEL_NAME"
          value = "titanic-survival"
        }
        env {
          name  = "MODEL_VERSION"
          value = "1"
        }
      }
    }
  }
}
```

Repeat for `staging` and `prod` environments with appropriate naming.

## Common Operations

### View Outputs

```bash
cd infra/envs/dev
terraform output
```

### View State

```bash
terraform show
terraform state list
```

### Import Existing Resources

```bash
# Example: Import existing GCS bucket
terraform import module.mlsys.google_storage_bucket.ml_models mlsys-models-dev
```

### Switch Environments

```bash
# No need to switch - each environment is a separate directory
cd infra/envs/dev     # Work on dev
cd infra/envs/staging  # Work on staging
cd infra/envs/prod     # Work on prod
```

### Destroy Resources (DANGEROUS)

```bash
# Only for dev/staging - NEVER for prod without explicit confirmation
cd infra/envs/dev
terraform destroy -var="project_id=soufianesys" -var="region=us-central1"
```

## Module Outputs

Each environment exposes these outputs from the mlsys module:

```hcl
output "models_bucket_name"       # GCS bucket for models
output "composer_bucket_name"     # GCS bucket for DAGs
output "artifact_registry_name"   # Docker repository name
output "bigquery_dataset_id"      # BigQuery dataset ID
output "model_registry_sa_email"  # Service account email
```

Access in other Terraform files via `module.mlsys.{output_name}`.

## Troubleshooting

### State Lock Issues

```bash
terraform force-unlock <lock-id>
```

### Backend Initialization Errors

```bash
terraform init -reconfigure -backend-config="bucket=mlsys-terraform-state-dev"
```

### Provider Version Conflicts

```bash
terraform init -upgrade
```

### Permission Errors

Verify you have required IAM roles:
- `roles/storage.admin` - For creating/managing buckets
- `roles/iam.serviceAccountAdmin` - For creating service accounts
- `roles/resourcemanager.projectIamAdmin` - For granting IAM roles

```bash
gcloud projects get-iam-policy soufianesys \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)"
```

## Best Practices

1. **Always run `terraform plan` before `terraform apply`**
2. **Use command-line variables in CI/CD** (not terraform.tfvars)
3. **Never commit `terraform.tfvars` to version control**
4. **Keep Terraform version consistent** (use `.terraform-version`)
5. **Test in dev → staging → prod progression**
6. **Use modules for reusable infrastructure patterns**
7. **Separate environment state for complete isolation**
8. **Add model-specific resources in environment files, not the module**

## Module Design Philosophy

The `mlsys` module contains **only the base infrastructure** required for the platform:
- Storage (GCS, Artifact Registry)
- Data warehouse (BigQuery)
- Service accounts for platform services (model registry)

**Model-specific resources** (DAG service accounts, Cloud Run jobs, etc.) should be added:
- In environment-specific files (`envs/{dev,staging,prod}/*.tf`)
- NOT in the mlsys module
- This keeps the module clean and reusable

## Next Steps

1. Create Terraform state buckets (see Prerequisites)
2. Deploy dev environment to test module
3. Deploy staging environment for pre-production
4. Deploy prod environment when ready
5. Add model-specific resources as needed
6. Configure CI/CD workflows to automate deployments
