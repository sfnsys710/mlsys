# mlsys

ML system for machine learning development and deployment on GCP

## Overview

**Purpose**: End-to-end ML platform for developing models locally and deploying them as HTTP services on Google Cloud Platform.

**Key Technologies**:
- Python 3.12 with uv package manager (fast, modern dependency management)
- ML: scikit-learn, pandas, numpy, matplotlib
- GCP: BigQuery, Cloud Storage, Cloud Run Service, Artifact Registry
- Web: FastAPI (HTTP endpoints for predictions and model registry)
- Infrastructure: Terraform 1.10.0
- CI/CD: GitHub Actions with smart change detection
- Containers: Docker multi-stage builds

**GCP Project**: `<your-gcp-project-id>` (single project, resources suffixed with `-dev`, `-staging`, `-prod`)

## Architecture

### Local Development
```
BigQuery (data) → Jupyter Notebook (EDA + training) → GCS (model artifacts)
```

### Production Deployment
```
GitHub PR → CI/CD → Cloud Run Service (FastAPI)
                            ↓
                    GET /predict → BigQuery predictions
                    GET /model-registry → BigQuery registry
                    GET /health → Health check
```

### Progressive Deployment
```
dev (automatic on PR push) → staging (manual) → prod (manual)
```

## First-Time Setup

⚠️ **One-time manual setup required** before using this project.

### Prerequisites

- GCP Project created (e.g., `<your-gcp-project-id>`)
- `gcloud` CLI installed and authenticated
- Owner or Editor role on the GCP project
- Terraform 1.10.0 installed
- uv package manager installed

### 1. Local Setup

```bash
# 1. Install dependencies
uv sync --group dev --group pre-commit --group test

# 2. Install pre-commit hooks
uv run pre-commit install

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your GCP project details

# 4. Verify setup by running tests
uv run pytest
```

### 2. Create Terraform State Buckets

```bash
# Create state buckets
gcloud storage buckets create gs://mlsys-terraform-state-dev --location=<your-gcp-region> --uniform-bucket-level-access
gcloud storage buckets create gs://mlsys-terraform-state-staging --location=<your-gcp-region> --uniform-bucket-level-access
gcloud storage buckets create gs://mlsys-terraform-state-prod --location=<your-gcp-region> --uniform-bucket-level-access

# Enable versioning
gcloud storage buckets update gs://mlsys-terraform-state-dev --versioning
gcloud storage buckets update gs://mlsys-terraform-state-staging --versioning
gcloud storage buckets update gs://mlsys-terraform-state-prod --versioning
```

### 3. Create GitHub Actions Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Service Account"

# Grant necessary roles for CI/CD operations
# Terraform state management
gcloud projects add-iam-policy-binding <your-gcp-project-id> \
  --member="serviceAccount:github-actions@<your-gcp-project-id>.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Artifact Registry (Docker images)
gcloud projects add-iam-policy-binding <your-gcp-project-id> \
  --member="serviceAccount:github-actions@<your-gcp-project-id>.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Cloud Run deployment
gcloud projects add-iam-policy-binding <your-gcp-project-id> \
  --member="serviceAccount:github-actions@<your-gcp-project-id>.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Service Account management (for Cloud Run)
gcloud projects add-iam-policy-binding <your-gcp-project-id> \
  --member="serviceAccount:github-actions@<your-gcp-project-id>.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# IAM management (for Terraform)
gcloud projects add-iam-policy-binding <your-gcp-project-id> \
  --member="serviceAccount:github-actions@<your-gcp-project-id>.iam.gserviceaccount.com" \
  --role="roles/iam.securityAdmin"

# BigQuery, GCS, and API management (for Terraform)
gcloud projects add-iam-policy-binding <your-gcp-project-id> \
  --member="serviceAccount:github-actions@<your-gcp-project-id>.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding <your-gcp-project-id> \
  --member="serviceAccount:github-actions@<your-gcp-project-id>.iam.gserviceaccount.com" \
  --role="roles/serviceusage.serviceUsageAdmin"

# Generate key (store in GitHub Secrets as GCP_SA_KEY)
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@<your-gcp-project-id>.iam.gserviceaccount.com
```

### 4. Configure GitHub Secrets and Variables

In your GitHub repository settings:

**Secrets** (Settings → Secrets and variables → Actions → Secrets):
- `GCP_SA_KEY`: Contents of `github-actions-key.json`

**Variables** (Settings → Secrets and variables → Actions → Variables):
- `GCP_PROJECT_ID`: Your GCP project ID (e.g., `<your-gcp-project-id>`)
- `GCP_REGION`: Your GCP region (e.g., `<your-gcp-region>`)

**Environment**: Create an environment named `gcp` in repository settings

### 5. Deploy Infrastructure

```bash
# Initialize and deploy dev environment
cd infra/envs/dev
terraform init
terraform apply -var="project_id=<your-gcp-project-id>" -var="region=<your-gcp-region>"

# Repeat for staging if needed (not recommended, staging and prod supposed to mangened automaticaly by CI/CD)
```

✅ **Setup complete!** You can now develop models and deploy to GCP.

## Development Workflow

### 1. Develop Model in Jupyter

See complete example: `notebooks/titanic-survival-example.ipynb`

```python
from mlsys.bq import bq_get
from mlsys.gcs import gcs_put_pickle
from mlsys.settings import GCS_BUCKET_MODELS_DEV
from sklearn.ensemble import RandomForestClassifier

# Download data from BigQuery
df = bq_get("SELECT * FROM <your-gcp-project-id>.titanic.train")

# Train model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Upload to GCS
gcs_put_pickle(model, GCS_BUCKET_MODELS_DEV, "titanic-survival/v1/model.pkl")
```

### 2. Create Pull Request

Create a new branch, commit your changes, and create a pull request.

**What happens automatically**:
- Pre-commit checks run (ruff, detect-secrets, nbstripout)
- Smart change detection determines what to deploy:
  - Changed `infra/`? → Deploy Terraform to dev
  - Changed `src/`, `api/`, `scripts/`? → Build Docker and deploy to dev
- Only changed components are deployed (efficient)

### 3. Test in Dev Environment

On each push to a PR that targets the main branch, the following happens:
- Terraform is deployed to dev
- Docker image is built and deployed to dev
- Cloud Run service is updated

**What you need to do**:
- Review the changes in the PR
- Test the model predictions in the PR

```bash
# Register the model
curl "https://mlsys-dev-xxxxx.run.app/model-registry?env=dev"

# Make predictions
curl "https://mlsys-dev-xxxxx.run.app/predict?env=dev&input_table=<your-gcp-project-id>.titanic.test&output_table=<your-gcp-project-id>.titanic.predictions&model_name=titanic-survival&model_version=v1"
```

### 4. Promote to Staging/Prod

Currently manual - run Terraform and redeploy:
```bash
cd infra/envs/staging
terraform apply -var="project_id=<your-gcp-project-id>" -var="region=<your-gcp-region>"
# Then rebuild and deploy Docker image with staging tag
```

## Project Structure

```
mlsys/
├── src/mlsys/               # Main Python package
│   ├── bq.py                # BigQuery I/O (bq_get, bq_put)
│   ├── gcs.py               # GCS I/O (gcs_get_pickle, gcs_put_pickle, gcs_list_blobs)
│   ├── vis.py               # Visualization helpers (not in production)
│   └── settings.py          # Configuration (loads from .env)
├── api/                     # FastAPI web service
│   └── main.py              # HTTP endpoints: /predict, /model-registry, /health
├── scripts/                 # Production scripts (invoked by API)
│   ├── predict.py           # Prediction pipeline
│   └── model_registry.py    # Model registration
├── tests/                   # Pytest test suite
│   ├── conftest.py          # Shared fixtures and mocks
│   ├── unit/                # Unit tests (36 tests)
│   │   ├── test_bq.py       # BigQuery I/O tests
│   │   ├── test_gcs.py      # GCS I/O tests
│   │   ├── test_predict.py  # Prediction pipeline tests
│   │   └── test_model_registry.py  # Model registry tests
│   └── integration/         # Integration tests (16 tests)
│       └── test_api.py      # FastAPI endpoint tests
├── notebooks/               # Jupyter notebooks for model development
│   └── titanic-survival-example.ipynb
├── infra/                   # Terraform infrastructure
│   ├── modules/mlsys/       # Reusable infrastructure module
│   └── envs/                # Environment configs (dev, staging, prod)
├── .github/workflows/       # CI/CD automation
│   └── pr.yml               # PR checks and dev deployment
├── Dockerfile               # Multi-stage container for Cloud Run
├── pyproject.toml           # Python dependencies (uv), pre-commit hooks and pytest configs
├── .pre-commit-config.yaml  # Code quality hooks
└── .env.example             # Environment variable template
```

## Common Commands

### Package Management (uv)

```bash
uv sync                          # Install/update dependencies
uv sync --group test             # Install test dependencies only
uv add <package>                 # Add new dependency to main group
uv add --group test <package>    # Add new test dependency
uv run python script.py          # Run Python script
```

### Code Quality

```bash
uv run pre-commit install                    # Install hooks
uv run pre-commit run --all-files            # Run all hooks manually
uv run pre-commit run ruff --all-files       # Run specific hook
```

### Infrastructure (Terraform)

```bash
cd infra/envs/dev
terraform init
terraform plan -var="project_id=<your-gcp-project-id>" -var="region=<your-gcp-region>"
terraform apply -var="project_id=<your-gcp-project-id>" -var="region=<your-gcp-region>"
terraform output                              # Show outputs
```

### Docker (Local Testing)

```bash
docker build -t mlsys:latest .
docker run -p 8080:8080 mlsys:latest
# Test: curl http://localhost:8080/health
```

### Testing

**Run all tests with coverage**:
```bash
uv run pytest                      # Run all tests
uv run pytest -m unit              # Run only unit tests
uv run pytest -m integration       # Run only integration tests
uv run pytest --no-cov             # Run without coverage (faster)
```

**View coverage report**:
```bash
# macOS - Default browser
open htmlcov/index.html
```

#### Why We Test This Way

**Fixtures** (`conftest.py`):
- Reusable test data (sample DataFrames, mock models)
- Consistent test setup across all tests
- Reduces code duplication
- Example: `sample_titanic_df` fixture provides the same test data to all prediction tests

**Mocks** (unittest.mock):
- Simulate external services (BigQuery, GCS) without real API calls
- Fast test execution (no network I/O)
- No GCP credentials needed for testing
- Predictable test results (no external dependencies)
- Example: Mock BigQuery client returns pre-defined DataFrame instead of querying actual BigQuery

**Unit Tests** (`@pytest.mark.unit`):
- Test individual functions in isolation
- Fast execution (< 1 second total)
- Verify business logic correctness
- Example: Test that `bq_put()` calls BigQuery API with correct parameters

**Integration Tests** (`@pytest.mark.integration`):
- Test how components work together
- Verify FastAPI endpoints route to correct scripts
- Ensure HTTP request/response contracts are correct
- Example: Test that `/predict` endpoint validates query parameters and calls `predict()` function

**Coverage Reports**:
- Identify untested code paths
- Ensure production code has test coverage
- HTML report shows line-by-line coverage with visual highlights
- Note: `vis.py` is excluded (not deployed to production)

## API Endpoints

### `GET /predict`

Make predictions on BigQuery data.

**Query Parameters**:
- `env` - Environment (dev, staging, or prod)
- `input_table` - Fully qualified input table (e.g., `project.dataset.input`)
- `output_table` - Fully qualified output table (e.g., `project.dataset.predictions`)
- `model_name` - Model name (e.g., `titanic-survival`)
- `model_version` - Model version (e.g., `v1`)

**Example**:
```bash
curl "https://mlsys-dev-xxxxx.run.app/predict?env=dev&input_table=<your-gcp-project-id>.titanic.test&output_table=<your-gcp-project-id>.titanic.predictions&model_name=titanic-survival&model_version=v1"
```

**What it does**:
1. Pulls data from BigQuery input table
2. Loads model from GCS (bucket determined by env)
3. Makes predictions
4. Adds metadata (timestamp, model name, version)
5. Pushes results to BigQuery output table

⚠️ **Note**: Currently hardcoded for Titanic model (expects `PassengerId`, produces `Survived` with prediction probability). See `scripts/predict.py:80-86` for implementation details. Generalization needed for other models.

### `GET /model-registry`

Scan GCS bucket and register all models in BigQuery.

**Query Parameters**:
- `env` - Environment (dev, staging, or prod)

**Example**:
```bash
curl "https://mlsys-dev-xxxxx.run.app/model-registry?env=dev"
```

**What it does**:
1. Lists all blobs in `mlsys-models-{env}` bucket
2. Filters for `.pkl` files matching: `{model_name}/v{version}/model.pkl`
3. Reads optional `metadata.json` from same directory
4. Upserts to `mlsys_{env}.model_registry` BigQuery table

### `GET /health`

Health check endpoint for Cloud Run.

```bash
curl "https://mlsys-dev-xxxxx.run.app/health"
```

## Naming Conventions

### GCP Resources (per environment)
- **Cloud Run Service**: `mlsys-{env}` (e.g., `mlsys-dev`)
- **Artifact Registry**: `mlsys-{env}`
- **GCS Bucket**: `mlsys-models-{env}`
- **BigQuery Dataset**: `mlsys_{env}` (note: underscore, not hyphen)
- **Service Account**: `mlsys-sa-{env}@<your-gcp-project-id>.iam.gserviceaccount.com`

### Model Artifacts in GCS
- **Path pattern**: `{model-name}/v{version}/model.pkl`
- **Model name**: lowercase, hyphen-separated (e.g., `titanic-survival`)
- **Version**: `v1`, `v2`, `v3`, etc.
- **Example**: `gs://mlsys-models-dev/titanic-survival/v1/model.pkl`
- **Optional**: `gs://mlsys-models-dev/titanic-survival/v1/metadata.json`

### Notebooks
- **Pattern**: `{usecase}-{purpose}.ipynb`
- **Examples**:
  - `titanic-survival-example.ipynb`

## CI/CD Pipeline

### PR Workflow (Automatic)

**Trigger**: Pull request to `main` branch

**Pipeline**:
1. Pre-commit checks (ruff, detect-secrets, nbstripout)
2. Change detection:
   - `infra/**` → Deploy Terraform to dev
   - `src/**, api/**, scripts/**, Dockerfile, pyproject.toml, uv.lock` → Build Docker, deploy to dev
3. Selective deployment (only changed components)

**Benefits**:
- Fast feedback (only deploys what changed)
- Automatic dev deployment on PR push (opened, synchronize, reopened)
- Clear CI/CD logs showing what was deployed

### Manual Staging/Prod Deployment

Currently manual process:
1. Update infrastructure: `terraform apply` in `infra/envs/{env}/`
2. Build and push Docker image with version tag
3. Update Cloud Run service to use new image

## Infrastructure (Terraform)

### Managed Resources

The `mlsys` Terraform module creates per environment:

- **GCS Buckets**:
  - `mlsys-models-{env}` - Model artifacts (versioning enabled)

- **BigQuery**:
  - Dataset: `mlsys_{env}`
  - Table: `model_registry` (partitioned by date, clustered by model name)

- **Artifact Registry**:
  - Repository: `mlsys-{env}` (Docker images)

- **Cloud Run Service**:
  - Service: `mlsys-{env}` (FastAPI container)
  - Note: Image managed by CI/CD, Terraform ignores drift

- **Service Account**:
  - `mlsys-sa-{env}` with roles:
    - `roles/bigquery.dataEditor` - Read/write BigQuery
    - `roles/bigquery.jobUser` - Run queries
    - `roles/storage.objectAdmin` - Full GCS access

### Terraform Commands

```bash
# Dev environment
cd infra/envs/dev
terraform init -backend-config="bucket=mlsys-terraform-state-dev"
terraform plan -var="project_id=<your-gcp-project-id>" -var="region=<your-gcp-region>"
terraform apply -var="project_id=<your-gcp-project-id>" -var="region=<your-gcp-region>"

# View outputs
terraform output

# State management
terraform show
terraform state list
```

### State Management

- Separate GCS buckets per environment
- Versioning enabled for rollback
- State locking via GCS (automatic)
- Complete environment isolation

## Docker Configuration

### Multi-Stage Build

**Builder stage** (`ghcr.io/astral-sh/uv:python3.12-bookworm-slim`):
- Fast dependency installation with uv (10-100x faster than pip)
- `UV_PYTHON_DOWNLOADS=0` - Use system Python 3.12
- `UV_COMPILE_BYTECODE=1` - Pre-compile for faster startup
- Dependencies installed first (better caching)

**Runtime stage** (`python:3.12-slim-bookworm`):
- Minimal image (~150MB)
- Copies only `.venv/`, `src/`, `scripts/`, `api/`
- Exposes port 8080
- Default CMD: `uvicorn api.main:app --host 0.0.0.0 --port 8080`

## Code Style

- **Line length**: 100 characters
- **Python version**: 3.12
- **Formatter**: Ruff
- **Linting rules**: E, W, F, I, B, C4, UP
- **Type hints**: Encouraged but not enforced

### Pre-commit Hooks

Automatically run on `git commit`:
- **File hygiene**: trailing-whitespace, end-of-file-fixer
- **Validation**: check-yaml, check-toml, check-json
- **Python**: ruff (lint + format)
- **Security**: detect-secrets (use `# pragma: allowlist secret` for false positives)
- **Notebooks**: nbqa-ruff, nbstripout (preserves outputs, strips metadata)

## Environment Variables

Key variables (see `.env.example` for full template):

```bash
# GCP Configuration
# Set these via GitHub secrets/variables for CI/CD
# For local development, copy .env.example to .env and fill in your values
GCP_PROJECT_ID=<your-gcp-project>
GCP_REGION=<your-gcp-region>

# GCS Model Buckets
# Default values are set in settings.py, override if needed
GCS_BUCKET_MODELS_DEV=mlsys-models-dev
GCS_BUCKET_MODELS_STAGING=mlsys-models-staging
GCS_BUCKET_MODELS_PROD=mlsys-models-prod

# Terraform state buckets
TF_STATE_BUCKET_DEV=mlsys-terraform-state-dev
TF_STATE_BUCKET_STAGING=mlsys-terraform-state-staging
TF_STATE_BUCKET_PROD=mlsys-terraform-state-prod

# BigQuery dataset
BQ_DATASET=mlsys

# Note: BigQuery table paths are NOT configured here
# They are passed explicitly to bq_get() and bq_put() functions
# Example: bq_get("SELECT * FROM project.dataset.table")
```

## Best Practices

### BigQuery
- Always pass full table paths: `project.dataset.table`
- Use `bq_get(query: str) -> pd.DataFrame` for reads
  - Executes SQL query and returns results as DataFrame
  - Example: `df = bq_get("SELECT * FROM project.dataset.table LIMIT 10")`
- Use `bq_put(df: pd.DataFrame, table_id: str, write_disposition: str = "WRITE_APPEND")` for writes
  - Write dispositions: `WRITE_APPEND`, `WRITE_TRUNCATE`, `WRITE_EMPTY`
  - Example: `bq_put(df, "project.dataset.table", "WRITE_TRUNCATE")`

### GCS
- Store models in versioned folders: `{model-name}/v{N}/model.pkl`
- Use `gcs_get_pickle(bucket_name: str, blob_path: str) -> Any` for downloading pickled models
  - Downloads and deserializes pickled objects
  - Example: `model = gcs_get_pickle("mlsys-models-dev", "titanic-survival/v1/model.pkl")`
- Use `gcs_put_pickle(obj: Any, bucket_name: str, blob_path: str)` for uploading pickled models
  - Serializes and uploads objects using joblib
  - Example: `gcs_put_pickle(model, "mlsys-models-dev", "titanic-survival/v1/model.pkl")`
- Use `gcs_get(bucket_name: str, blob_path: str) -> bytes` for raw bytes (e.g., JSON metadata)
- Use `gcs_put(content: bytes | str, bucket_name: str, blob_path: str)` for uploading raw bytes/strings
- Use `gcs_list_blobs(bucket_name: str) -> list[Blob]` to list all blobs in a bucket

### Notebook Development
- Use notebooks for EDA and experimentation only
- Keep production code in `src/mlsys/`, `api/`, `scripts/`
- Extract reusable functions to modules
- Follow naming convention: `{usecase}-{purpose}.ipynb`
- See `notebooks/titanic-survival-example.ipynb` for complete example

### Testing
- **Unit and integration tests**: Run `uv run pytest` before committing changes
- **Pre-commit hooks**: Run automatically on commit
- **Manual checks**: `uv run pre-commit run --all-files`
- **Coverage**: View HTML report with `open htmlcov/index.html`
- **Deployment testing**: Always test in dev environment before promoting to staging/prod
- **Test philosophy**:
  - Write tests for all production code (scripts/, src/mlsys/, api/)
  - Use fixtures for reusable test data
  - Mock external services (BigQuery, GCS) to avoid API calls
  - Aim for 100% coverage of production code

## Troubleshooting

### Pre-commit Hook Failures
- **detect-secrets**: Add `# pragma: allowlist secret` for false positives
- **ruff**: Fix code or add `# noqa: <code>` if intentional
- **nbstripout**: Ensure notebooks are in proper format

### Docker Build Issues
- Verify Python version consistency (3.12 everywhere)
- Check layer caching (dependencies before code)
- Validate `UV_PYTHON_DOWNLOADS=0` and `UV_COMPILE_BYTECODE=1`

### Terraform Issues
```bash
# State lock
terraform force-unlock <lock-id>

# Reinitialize
terraform init -reconfigure -backend-config="bucket=mlsys-terraform-state-dev"

# Upgrade providers
terraform init -upgrade
```

### Test Failures
```bash
# Run tests with verbose output
uv run pytest -vv

# Run specific test file
uv run pytest tests/unit/test_bq.py -v

# Run specific test function
uv run pytest tests/unit/test_bq.py::TestBqGet::test_bq_get_success -v

# Show full traceback
uv run pytest --tb=long

# Run without coverage (faster, easier debugging)
uv run pytest --no-cov -vv
```

## License

MIT License

**Happy ML dev and deployment with MLSys**
