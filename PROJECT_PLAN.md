# ML System Repository - Implementation Plan

## Project Overview

Repository for machine learning development in Jupyter notebooks and deployment to GCP with scheduled predictions.

### Key Configuration
- **Python Version**: 3.12
- **GCP Project**: shoufianesys (same project, resources suffixed with -dev/-staging/-prod)
- **Example Model**: titanic-survival
- **Package Manager**: uv
- **Environments**: dev, staging, prod

## Architecture

### Local Workflow
1. Download data from BigQuery using utility functions
2. EDA and ML model selection in Jupyter notebooks
3. Upload ML model artifacts to GCS

### GCP Workflow
- **Environments**: dev, staging, and prod (same project, different resources)
- **Orchestration**: Airflow Composer with model-specific DAGs
- **Compute**: Cloud Run jobs with Docker containers
- **CI/CD**: GitHub Actions for progressive deployment
- **Data**: BigQuery tables managed by data engineering team (full table paths passed explicitly)

### Repository Structure
```
mlsys/
├── .github/
│   └── workflows/           # CI/CD workflows
├── mlsys/                   # Main Python package (managed by uv)
│   ├── vis/                 # Visualization helpers
│   ├── bq/                  # BigQuery I/O (bq_get, bq_put)
│   ├── gcs/                 # GCS I/O (gcs_get, gcs_put)
│   └── settings.py          # Configuration management
├── infra/                   # Terraform infrastructure
├── dags/                    # Airflow DAGs (one per model)
├── notebooks/               # Jupyter notebooks for analysis
├── scripts/                 # Deployment scripts
│   ├── predict.py           # pull_predict_push() function
│   └── model_registry/      # Cloud Function for model registry
├── Dockerfile               # Container for Cloud Run jobs
├── .pre-commit-config.yaml  # Pre-commit hooks
└── .env.example             # Environment variable template
```

## Naming Conventions

For each model (e.g., titanic-survival):
- **DAG Name**: `titanic-survival-{env}` (e.g., `titanic-survival-dev`, `titanic-survival-staging`, `titanic-survival-prod`)
- **GCS Path**: `gs://ml-models-{env}/titanic-survival/v1/`, `gs://ml-models-{env}/titanic-survival/v2/`, etc.
- **CI/CD Job**: `deploy-titanic-survival-{env}`
- **Service Account**: `titanic-survival-dag-sa-{env}@shoufianesys.iam.gserviceaccount.com`
- **BigQuery Tables**: Managed by data engineering team, full paths passed explicitly (e.g., `project.dataset.table`)

## Key Scripts

### `scripts/predict.py` - `pull_predict_push()`
1. Pull data from BigQuery
2. Pull model artifacts from GCS
3. Make predictions
4. Add metadata (timestamp, model name, model version)
5. Push predictions back to BigQuery

### `scripts/model_registry/` - Cloud Function
- Event-based trigger on new object in `ml-models-{dev/staging/prod}` buckets
- Registers model metadata in registry
- Updates model inventory

## Development Commands

### Package Management
```bash
uv sync                    # Install all dependencies (respects uv.lock)
uv add <package-name>      # Add new dependency and update uv.lock
uv run python script.py    # Run Python scripts
uv run jupyter lab         # Launch Jupyter for notebooks
```

### Pre-commit Hooks
```bash
uv run pre-commit install              # Install hooks (runs on git commit)
uv run pre-commit run --all-files      # Run all hooks manually
uv run pre-commit run ruff --all-files # Run specific hook
```

## Implementation Plan: 17 PRs

### Phase 1: Foundation (PRs 1-4)

#### PR #1: Setup uv Package Structure
**Branch**: `setup-uv-package-structure`
**Files**:
- `pyproject.toml` (uv with Python 3.12, build-system = uv_build)
- `.gitignore`
- `mlsys/__init__.py`
- Folder structure (empty folders with .gitkeep)

**Key Config**:
- Build backend: `uv_build`
- Python: `>=3.12`
- Package manager: `uv`

**Commit**: "Setup uv package structure with Python 3.12"

---

#### PR #2: Add Pre-commit Hooks
**Branch**: `add-precommit-hooks`
**Files**:
- `.pre-commit-config.yaml`

**Hooks**:
- **File hygiene**: trailing-whitespace, end-of-file-fixer, mixed-line-ending
- **Validation**: check-yaml, check-toml, check-json, check-added-large-files, check-merge-conflict
- **Python**: ruff (lint + format)
- **Security**: detect-secrets (use `# pragma: allowlist secret` for false positives)
- **Notebooks**: nbqa-ruff, nbqa-ruff-format, nbstripout (preserve outputs, strip metadata)

**Commit**: "Add comprehensive pre-commit hooks for code quality"

---

#### PR #3: Add CLAUDE.md Documentation
**Branch**: `add-claude-documentation`
**Files**:
- `CLAUDE.md` (comprehensive guide for AI assistants)

**Contents**:
- Project overview and architecture
- Development commands and workflows
- GCP resources and naming conventions
- Code style and patterns
- Infrastructure details

**Commit**: "Add CLAUDE.md for AI assistant guidance"

---

#### PR #4: Add Settings and Environment Config
**Branch**: `add-settings-environment`
**Files**:
- `mlsys/settings.py` (Pydantic settings with GCP config)
- `.env.example` (comprehensive template with all required vars)
- Updated `pyproject.toml` (add python-dotenv, pydantic-settings)

**Environment Variables**:
```bash
# GCP Configuration
GCP_PROJECT_ID=shoufianesys
GCP_REGION=us-central1

# GCS Model Buckets
GCS_BUCKET_MODELS_DEV=ml-models-dev
GCS_BUCKET_MODELS_STAGING=ml-models-staging
GCS_BUCKET_MODELS_PROD=ml-models-prod

# Airflow Composer
COMPOSER_BUCKET_DEV=<composer-bucket-dev>
COMPOSER_BUCKET_STAGING=<composer-bucket-staging>
COMPOSER_BUCKET_PROD=<composer-bucket-prod>

# Note: BigQuery table paths are passed explicitly to functions
# Example: bq_get("project_id.dataset.table")
```

**Commit**: "Add settings management with environment variables"

---

### Phase 2: Core Utilities (PRs 5-7)

#### PR #5: Add BigQuery I/O Utilities
**Branch**: `add-bigquery-io`
**Files**:
- `mlsys/bq/__init__.py`
- `mlsys/bq/io.py` (bq_get, bq_put functions)
- Updated `pyproject.toml` (add google-cloud-bigquery, pandas, pyarrow)

**Functions**:
- `bq_get(query)`: Execute query and return DataFrame (table paths explicitly in query)
- `bq_put(df, table_id, write_disposition)`: Upload DataFrame to BigQuery (full table_id: `project.dataset.table`)

**Commit**: "Add BigQuery I/O utilities"

---

#### PR #6: Add GCS I/O Utilities
**Branch**: `add-gcs-io`
**Files**:
- `mlsys/gcs/__init__.py`
- `mlsys/gcs/io.py` (gcs_get, gcs_put functions)
- Updated `pyproject.toml` (add google-cloud-storage, joblib, pickle)

**Functions**:
- `gcs_get(bucket_name, blob_path)`: Download model artifacts
- `gcs_put(obj, bucket_name, blob_path)`: Upload model artifacts

**Commit**: "Add GCS I/O utilities for model artifacts"

---

#### PR #7: Add Visualization Helpers
**Branch**: `add-visualization-helpers`
**Files**:
- `mlsys/vis/__init__.py`
- `mlsys/vis/plots.py` (common plotting functions)
- Updated `pyproject.toml` (add matplotlib, seaborn, plotly)

**Commit**: "Add visualization helper utilities"

---

### Phase 3: Containerization (PR 8)

#### PR #8: Add Docker Setup for Cloud Run
**Branch**: `add-docker-setup`
**Files**:
- `Dockerfile` (multi-stage build, optimized for Cloud Run)
- `.dockerignore`

**Dockerfile Features** (following PairReader pattern):
- **Builder stage**: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
  - `UV_PYTHON_DOWNLOADS=0`: Force use of system Python 3.12
  - `UV_COMPILE_BYTECODE=1`: Pre-compile bytecode for faster startup
  - Install dependencies first for better layer caching
- **Runtime stage**: `python:3.12-slim-bookworm`
  - Minimal runtime image
  - Copy only necessary files from builder

**Commit**: "Add multi-stage Dockerfile for Cloud Run jobs"

---

### Phase 4: Core Scripts (PRs 9-10)

#### PR #9: Add Prediction Script
**Branch**: `add-prediction-script`
**Files**:
- `scripts/predict.py` (pull_predict_push function)
- `scripts/__init__.py`
- `scripts/README.md` (usage instructions)

**Commit**: "Add prediction script for Cloud Run jobs"

---

#### PR #10: Add Model Registry Cloud Function
**Branch**: `add-model-registry-function`
**Files**:
- `scripts/model_registry/main.py` (Cloud Function entrypoint)
- `scripts/model_registry/requirements.txt`
- `scripts/model_registry/README.md` (deployment guide with gcloud commands)

**Commit**: "Add Cloud Function for model registry"

---

### Phase 5: Infrastructure as Code (PRs 11-12)

#### PR #11: Add Terraform Base Infrastructure
**Branch**: `add-terraform-base`
**Files**:
- `infra/.terraform-version` (version management, used by CI/CD)
- `infra/terraform.tfvars.example` (local dev template)
- `infra/main.tf`
- `infra/variables.tf`
- `infra/outputs.tf`
- `infra/backend.tf` (GCS state backend - separate buckets for dev/prod)
- `infra/provider.tf`
- `infra/gcs_buckets.tf` (ml-models-dev, ml-models-prod)
- `infra/README.md` (setup instructions, secret management via gcloud)

**Key Design**:
- Separate state buckets per environment: `sfn-terraform-state-dev`, `sfn-terraform-state-staging`, `sfn-terraform-state-prod`
- Manual secret management (NOT in Terraform) via `gcloud secrets`
- Local dev uses `terraform.tfvars`, CI/CD uses command-line variables
- Resources per environment: GCS buckets (`ml-models-{env}`), Artifact Registry, service accounts

**Commit**: "Add Terraform base infrastructure with GCS buckets"

---

#### PR #12: Add Terraform Service Accounts Module
**Branch**: `add-terraform-service-accounts`
**Files**:
- `infra/modules/model_service_account/main.tf`
- `infra/modules/model_service_account/variables.tf`
- `infra/modules/model_service_account/outputs.tf`
- `infra/service_accounts.tf` (titanic-survival-dag-sa for dev, staging & prod with IAM roles)

**Commit**: "Add Terraform module for model service accounts"

---

### Phase 6: CI/CD (PRs 13-15)

#### PR #13: Add Reusable Docker Build Workflow
**Branch**: `add-docker-build-workflow`
**Files**:
- `.github/workflows/docker-build.yml` (reusable workflow)

**Features**:
- Parameterized by environment (dev/prod)
- Build and push to Artifact Registry
- Tag with commit SHA or version
- Code change detection (skip if only docs/infra changed)

**Commit**: "Add reusable Docker build workflow"

---

#### PR #14: Add Reusable Terraform Workflow
**Branch**: `add-terraform-workflow`
**Files**:
- `.github/workflows/terraform-workflow.yml` (reusable workflow)

**Features**:
- Terraform format, validate, plan, apply
- Parameterized by environment
- Uses `.terraform-version` file
- Command-line variables (not tfvars)

**Commit**: "Add reusable Terraform workflow"

---

#### PR #15: Add Main CI/CD Workflows
**Branch**: `add-main-cicd-workflows`
**Files**:
- `.github/workflows/pr.yml` (auto-deploy to dev on PR)
- `.github/workflows/staging.yml` (manual staging deployment)
- `.github/workflows/prod.yml` (manual prod deployment with confirmation)
- `.github/workflows/deploy-dag.yml` (manual DAG deployment)

**Features**:
- **PR workflow**: Pre-commit checks → Terraform (dev) → Docker (dev) - with code change detection
- **Staging workflow**: Manual trigger → Terraform (staging) → Docker (staging)
- **Prod workflow**: Manual trigger with "production" confirmation input → Terraform → Docker
- **DAG workflow**: Manual trigger to sync DAG to Composer bucket (env selection)

**Commit**: "Add main CI/CD workflows for multi-environment deployment"

---

### Phase 7: Repository Governance (PR 16)

#### PR #16: Add Repository Governance
**Branch**: `add-repository-governance`
**Files**:
- `.github/CODEOWNERS` (designate code owners)

**Contents**:
```
* @your-github-username
/infra/ @your-github-username
/.github/ @your-github-username
```

**Branch Protection** (configure via GitHub UI after merge):
- Rebase-only merges for linear git history
- 1 code owner approval required
- CI must pass (pre-commit + tests)
- Secret scanning enabled

**Commit**: "Add repository governance with CODEOWNERS"

---

### Phase 8: Application Layer (PR 17)

#### PR #17: Add Titanic Survival DAG and Notebooks
**Branch**: `add-titanic-dag-notebooks`
**Files**:
- `dags/titanic_survival_dag.py` (environment-aware)
- `notebooks/.gitkeep`
- `notebooks/README.md` (structure guidelines)
- `notebooks/00_template.ipynb` (starter template)

**DAG Features**:
- Environment detection (dev/prod)
- Triggers Cloud Run job
- Passes model name and version as env vars
- Configurable schedule

**Commit**: "Add titanic-survival DAG and notebooks structure"

---

## CI/CD Architecture

### Modular Reusable Workflow Design

Following PairReader's pattern, we use a **three-tier workflow architecture**:

**Main Workflows** (trigger deployments):
- `pr.yml`: Auto-deploy to dev on PR to main
- `staging.yml`: Manual staging deployment
- `prod.yml`: Manual prod deployment with confirmation
- `deploy-dag.yml`: Manual DAG deployment

**Reusable Components** (called by main workflows):
- `terraform-workflow.yml`: Parameterized Terraform operations
- `docker-build.yml`: Parameterized Docker build/push

**Benefits**:
- DRY principle: Logic defined once, reused across environments
- Consistency: Same process for all environments
- Maintainability: Changes propagate automatically

### Progressive Deployment Strategy

**dev → staging → prod**

1. **Dev Environment** (Automatic on PR):
   - Pre-commit checks
   - Terraform plan/apply (dev)
   - Code change detection
   - Docker build/push (only if code changed)
   - Tag: `{git-sha}`
   - Access: Public/unauthenticated for easy testing

2. **Staging Environment** (Manual trigger):
   - Terraform plan/apply (staging)
   - Docker build/push
   - Tag: `v{version}` from pyproject.toml
   - Access: Public/unauthenticated for pre-production testing
   - Use case: Final validation before production

3. **Prod Environment** (Manual with confirmation):
   - Requires typing "production" to confirm
   - Terraform plan/apply (prod)
   - Docker build/push
   - Tag: `v{version}` from pyproject.toml
   - Access: Private/authenticated for production security
   - Concurrency protection

### Code Change Detection

Smart detection avoids unnecessary Docker builds:
```yaml
files: |
  src/**
  mlsys/**
  scripts/**
  pyproject.toml
  uv.lock
  Dockerfile
```

If only infra/docs/tests change, Terraform runs but Docker build is skipped.

### GitHub Environment Configuration

**Required Environment** (GitHub repo settings):
- **`gcp`**: Single environment for all deployments
  - Secret: `SA` (GCP service account JSON key)
  - Variables: `GCP_PROJECT_ID`, `GCP_REGION`

## Enterprise Features

### Model Versioning
- Semantic versioning (v1, v2, v3, etc.)
- Stored in GCS folder structure: `gs://ml-models-{env}/{model-name}/v{N}/`
- Version passed to prediction script via DAG
- Tracked in model registry

### Model Registry
- Cloud Function triggered on GCS uploads to `ml-models-{dev/staging/prod}` buckets
- Tracks: model name, version, upload timestamp, file size, uploader, environment
- Stored in BigQuery table: `ml_registry.models`
- Queryable for model history and lineage across all environments

### Data Versioning
- Assumed to be handled externally (e.g., dbt snapshots)
- All predictions include timestamp metadata
- Prediction tables partitioned by prediction_timestamp

## Best Practices

### Docker
- Multi-stage builds for smaller images
- `UV_PYTHON_DOWNLOADS=0`: Force system Python (no version mismatch)
- `UV_COMPILE_BYTECODE=1`: Pre-compile for faster startup
- Layer caching: Install deps first, copy code last

### Terraform
- State per environment: `sfn-terraform-state-{env}` (dev, staging, prod)
- Version management via `.terraform-version`
- Secrets managed manually via `gcloud secrets` (NOT in Terraform)
- Local dev: `terraform.tfvars`, CI/CD: command-line vars
- Separate workspace directories for each environment

### Pre-commit Hooks
- File hygiene, validation, Python formatting, security, notebooks
- Use `# pragma: allowlist secret` for false positive secrets
- Use `# noqa: <code>` for intentional violations

## Notes

- Models are trained/evaluated with the latest available data before artifact upload
- Each model deployment requires: DAG creation, CI/CD job, Terraform service account, trained model in GCS
- Infrastructure optimized for enterprise-grade system with proper IAM, versioning, and monitoring hooks
- All Python versions MUST match: pyproject.toml, Dockerfile builder, Dockerfile runtime

## Next Steps After Plan Execution

1. Configure GitHub environment `gcp` with service account secret
2. Create Terraform state buckets manually: `sfn-terraform-state-dev`, `sfn-terraform-state-staging`, `sfn-terraform-state-prod`
3. Train titanic-survival model in notebook
4. Upload artifacts to GCS: `gs://ml-models-dev/titanic-survival/v1/`
5. Open PR to trigger dev deployment
6. Test prediction pipeline in dev
7. Manual trigger staging deployment for validation
8. Manual trigger prod deployment with confirmation
9. Set up monitoring and alerting
