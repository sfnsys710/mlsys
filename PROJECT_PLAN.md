# ML System Repository - Implementation Plan

## Project Overview

Repository for machine learning development in Jupyter notebooks and deployment to GCP with scheduled predictions.

### Key Configuration
- **Python Version**: 3.12
- **GCP Project**: shoufianesys (same project, resources suffixed with -dev/-prod)
- **Example Model**: titanic-survival
- **Package Manager**: uv

## Architecture

### Local Workflow
1. Download data from BigQuery using utility functions
2. EDA and ML model selection in Jupyter notebooks
3. Upload ML model artifacts to GCS

### GCP Workflow
- **Environments**: dev and prod (same project, different resources)
- **Orchestration**: Airflow Composer with model-specific DAGs
- **Compute**: Cloud Run jobs with Docker containers
- **CI/CD**: GitHub Actions for DAG deployment (manual trigger)

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
- **DAG Name**: `titanic-survival-dev` / `titanic-survival-prod`
- **GCS Path**: `gs://ml-models-dev/titanic-survival/v1/`, `gs://ml-models-dev/titanic-survival/v2/`, etc.
- **CI/CD Job**: `deploy-titanic-survival-dev` / `deploy-titanic-survival-prod`
- **Service Account**: `titanic-survival-dag-sa@shoufianesys.iam.gserviceaccount.com`

## Key Scripts

### `scripts/predict.py` - `pull_predict_push()`
1. Pull data from BigQuery
2. Pull model artifacts from GCS
3. Make predictions
4. Add metadata (timestamp, model name, model version)
5. Push predictions back to BigQuery

### `scripts/model_registry/` - Cloud Function
- Event-based trigger on new object in `ml-models-{dev/prod}` buckets
- Registers model metadata in registry
- Updates model inventory

## Implementation Plan: 15 PRs

### Phase 1: Foundation (PRs 1-3)

#### PR #1: Initial Project Structure
**Branch**: `01-init-project`
**Files**:
- `pyproject.toml` (uv with Python 3.12)
- `.gitignore`
- `README.md`
- `mlsys/__init__.py`
- Folder structure (empty folders with .gitkeep)

**Commit**: "Initialize project structure with uv and Python 3.12"

---

#### PR #2: Pre-commit Setup
**Branch**: `02-pre-commit`
**Files**:
- `.pre-commit-config.yaml`

**Hooks**:
- ruff (format + lint)
- trailing-whitespace
- end-of-file-fixer
- check-yaml
- check-toml
- nbstripout (notebook cleaning)
- detect-secrets

**Commit**: "Add pre-commit hooks for code quality"

---

#### PR #3: Environment & Settings
**Branch**: `03-settings-env`
**Files**:
- `mlsys/settings.py` (Pydantic settings with GCP config)
- `.env.example`
- Updated `pyproject.toml` (add python-dotenv, pydantic-settings)

**Commit**: "Add settings management with environment variables"

---

### Phase 2: Core Utilities (PRs 4-6)

#### PR #4: BigQuery I/O
**Branch**: `04-bigquery-io`
**Files**:
- `mlsys/bq/__init__.py`
- `mlsys/bq/io.py` (bq_get, bq_put functions)
- Updated `pyproject.toml` (add google-cloud-bigquery, pandas)

**Commit**: "Add BigQuery I/O utilities"

---

#### PR #5: GCS I/O
**Branch**: `05-gcs-io`
**Files**:
- `mlsys/gcs/__init__.py`
- `mlsys/gcs/io.py` (gcs_get, gcs_put functions)
- Updated `pyproject.toml` (add google-cloud-storage, joblib)

**Commit**: "Add GCS I/O utilities for model artifacts"

---

#### PR #6: Visualization Helpers
**Branch**: `06-viz-helpers`
**Files**:
- `mlsys/vis/__init__.py`
- `mlsys/vis/plots.py` (common plotting functions)
- Updated `pyproject.toml` (add matplotlib, seaborn)

**Commit**: "Add visualization helper utilities"

---

### Phase 3: Containerization (PR 7)

#### PR #7: Docker Setup
**Branch**: `07-docker`
**Files**:
- `Dockerfile` (multi-stage build, Python 3.12, optimized for Cloud Run)
- `.dockerignore`

**Commit**: "Add Dockerfile for Cloud Run jobs"

---

### Phase 4: Core Scripts (PRs 8-9)

#### PR #8: Prediction Script
**Branch**: `08-predict-script`
**Files**:
- `scripts/predict.py` (pull_predict_push function)
- `scripts/__init__.py`

**Commit**: "Add prediction script for Cloud Run jobs"

---

#### PR #9: Model Registry Function
**Branch**: `09-model-registry`
**Files**:
- `scripts/model_registry/main.py` (Cloud Function entrypoint)
- `scripts/model_registry/requirements.txt`
- `scripts/model_registry/README.md` (deployment instructions)

**Commit**: "Add Cloud Function for model registry"

---

### Phase 5: Infrastructure as Code (PRs 10-11)

#### PR #10: Terraform Base
**Branch**: `10-terraform-base`
**Files**:
- `infra/main.tf`
- `infra/variables.tf`
- `infra/outputs.tf`
- `infra/backend.tf` (GCS state backend)
- `infra/provider.tf`
- `infra/gcs_buckets.tf` (ml-models-dev, ml-models-prod)

**Commit**: "Add Terraform base infrastructure with GCS buckets"

---

#### PR #11: Service Accounts Terraform
**Branch**: `11-terraform-sa`
**Files**:
- `infra/modules/model_service_account/main.tf`
- `infra/modules/model_service_account/variables.tf`
- `infra/modules/model_service_account/outputs.tf`
- `infra/service_accounts.tf` (titanic-survival-dag-sa for dev & prod)

**Commit**: "Add Terraform module for model service accounts"

---

### Phase 6: CI/CD (PRs 12-13)

#### PR #12: Docker CI/CD
**Branch**: `12-docker-cicd`
**Files**:
- `.github/workflows/build-push-docker.yml`

**Triggers**: Push to main
**Steps**:
- Build Docker image
- Push to Artifact Registry
- Tag with commit SHA and 'latest'

**Commit**: "Add GitHub Actions workflow for Docker build/push"

---

#### PR #13: DAG Deployment Workflow
**Branch**: `13-dag-deployment`
**Files**:
- `.github/workflows/deploy-dag.yml`

**Triggers**: Manual (workflow_dispatch)
**Inputs**: model_name, environment (dev/prod)
**Steps**:
- Sync DAG to Composer GCS bucket

**Commit**: "Add manual workflow for DAG deployment"

---

### Phase 7: Application Layer (PRs 14-15)

#### PR #14: Sample DAG
**Branch**: `14-titanic-dag`
**Files**:
- `dags/titanic_survival_dag.py`

**Features**:
- Environment-aware (dev/prod)
- Triggers Cloud Run job
- Passes model name and version as env vars

**Commit**: "Add Airflow DAG for titanic-survival model"

---

#### PR #15: Notebooks Setup
**Branch**: `15-notebooks-setup`
**Files**:
- `notebooks/.gitkeep`
- `notebooks/README.md` (structure guidelines)
- `notebooks/00_template.ipynb` (starter template)

**Commit**: "Add notebooks folder with template"

---

## Enterprise Features

### Model Versioning
- Semantic versioning (v1, v2, v3, etc.)
- Stored in GCS folder structure
- Version passed to prediction script via DAG

### Model Registry
- Cloud Function triggered on GCS uploads
- Tracks: model name, version, upload timestamp, file size
- Stored in BigQuery table

### Data Versioning
- Assumed to be handled externally (e.g., dbt snapshots)
- Timestamps added to all predictions

## Notes

- Models are trained/evaluated with the latest available data before artifact upload
- Each model deployment requires: DAG creation, CI/CD job, Terraform service account, trained model in GCS
- Infrastructure optimized for enterprise-grade system with proper IAM, versioning, and monitoring hooks

## Next Steps After Plan Execution

1. Train titanic-survival model in notebook
2. Upload artifacts to GCS
3. Deploy DAG to Composer dev
4. Test prediction pipeline
5. Promote to prod
6. Add monitoring and alerting
