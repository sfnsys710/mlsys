# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Purpose**: ML system for training and deploying models on GCP

**Key Technologies**:
- Python 3.12 with uv package manager (fast, modern dependency management)
- ML Libraries: scikit-learn, pandas, numpy, matplotlib
- GCP: BigQuery, GCS, Cloud Run Service, Artifact Registry
- Web Framework: FastAPI (HTTP endpoints for predictions and model registry)
- Infrastructure: Terraform 1.10.0
- CI/CD: GitHub Actions with smart change detection
- Containerization: Docker multi-stage builds with uv

**GCP Project**: `<your-gcp-project-id>` (single project, resources suffixed with `-dev`, `-staging`, `-prod`)

## Architecture

### Local Workflow
1. Download data from BigQuery using `bq_get()` utility function
2. Perform EDA and ML model selection in Jupyter notebooks
3. Upload trained model artifacts to GCS using `gcs_put_pickle()`

### GCP Production Workflow
- **Environments**: dev, staging, and prod (same GCP project, different resources)
- **Compute**: Cloud Run Service running FastAPI in Docker container
- **Endpoints**:
  - `GET /predict` - Make predictions on BigQuery data
  - `GET /model-registry` - Scan GCS and register models in BigQuery
  - `GET /health` - Health check
- **CI/CD**: GitHub Actions with progressive deployment
- **Data**: BigQuery tables (full table paths passed explicitly to endpoints)

### Progressive Deployment Strategy
```
dev (automatic on PR push) → staging (manual from main) → prod (manual from main)
```

**Deployment strategy**:
- **Dev**: Automatically deploys on every PR push (opened, synchronize, reopened)
- **Staging**: Manual trigger only - After merging to main, manually trigger deployment from main branch
- **Prod**: Manual trigger only - After merging to main, manually trigger deployment from main branch

**How to deploy to staging/prod**:
1. Merge your PR to the main branch
2. Go to GitHub Actions → Select workflow (Staging/Production Deployment)
3. Click "Run workflow" → Select branch: **main** → Click "Run workflow"

**Versioning**: Update `version` in `pyproject.toml` before deploying to staging/prod. This version is used for Docker image tags (e.g., `0.2.0` → `mlsys-staging:0.2.0`, `mlsys-prod:0.2.0`).

### Deployment Flow
```
Jupyter → GCS Model Artifacts → Cloud Run Service (FastAPI)
                                      ↓
                    /predict → BigQuery Predictions
                    /model-registry → BigQuery Registry
```

## Repository Structure

```
mlsys/
├── .github/
│   └── workflows/           # CI/CD workflows (pr.yml, staging.yml, prod.yml)
├── src/mlsys/               # Main Python package (managed by uv)
│   ├── bq.py                # BigQuery I/O (bq_get, bq_put)
│   ├── gcs.py               # GCS I/O (gcs_get, gcs_put, gcs_get_pickle, gcs_put_pickle, gcs_list_blobs)
│   ├── vis.py               # Visualization helpers
│   └── settings.py          # Configuration management (loads from .env)
├── api/                     # FastAPI web service
│   └── main.py              # HTTP endpoints: /predict, /model-registry, /health
├── scripts/                 # Production scripts (invoked by API)
│   ├── predict.py           # Prediction pipeline (pull data, predict, push results)
│   └── model_registry.py    # Model registration (scan GCS, register in BigQuery)
├── tests/                   # Pytest test suite (52 tests)
│   ├── conftest.py          # Shared fixtures and mocks
│   ├── unit/                # Unit tests (36 tests)
│   │   ├── test_bq.py       # BigQuery I/O tests
│   │   ├── test_gcs.py      # GCS I/O tests
│   │   ├── test_predict.py  # Prediction pipeline tests
│   │   └── test_model_registry.py  # Model registry tests
│   └── integration/         # Integration tests (16 tests)
│       └── test_api.py      # FastAPI endpoint tests
├── infra/                   # Terraform infrastructure
│   ├── modules/mlsys/       # Reusable infrastructure module
│   └── envs/                # Environment-specific configs (dev, staging, prod)
├── notebooks/               # Jupyter notebooks for model development
│   └── titanic-survival-example.ipynb  # Complete example workflow
├── Dockerfile               # Multi-stage container for Cloud Run Service
├── .pre-commit-config.yaml  # Pre-commit hooks configuration
├── .env.example             # Environment variable template
└── CLAUDE.md                # This file
```

## Development Commands

### Package Management with uv
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

### Testing
```bash
uv run pytest                      # Run all tests with coverage
uv run pytest -m unit              # Run only unit tests
uv run pytest -m integration       # Run only integration tests
uv run pytest --no-cov             # Run without coverage (faster)
uv run pytest -vv                  # Verbose output
open htmlcov/index.html            # View coverage report (macOS)
```

### Running Scripts Locally (CLI)

The scripts in `scripts/` use [Python Fire](https://github.com/google/python-fire) to provide CLI interfaces. You can run them locally for testing or manual execution without going through the API.

#### Prediction Script (`scripts/predict.py`)

Run predictions locally using your local GCP credentials:

```bash
# Basic usage with named arguments
uv run python scripts/predict.py \
  --env=dev \
  --input_table="<your-gcp-project-id>.titanic.test" \
  --output_table="<your-gcp-project-id>.titanic.predictions" \
  --model_name="titanic-survival" \
  --model_version="v1"

# Alternative Fire syntax (positional arguments)
uv run python scripts/predict.py \
  dev \
  "<your-gcp-project-id>.titanic.test" \
  "<your-gcp-project-id>.titanic.predictions" \
  "titanic-survival" \
  "v1"

# Using different environments
uv run python scripts/predict.py \
  --env=staging \
  --input_table="<your-gcp-project-id>.titanic.test" \
  --output_table="<your-gcp-project-id>.titanic.predictions_staging" \
  --model_name="titanic-survival" \
  --model_version="v2"
```

#### Model Registry Script (`scripts/model_registry.py`)

Scan GCS bucket and register models locally:

```bash
# Register models in dev environment
uv run python scripts/model_registry.py --env=dev

# Alternative Fire syntax (positional argument)
uv run python scripts/model_registry.py dev

# Register models in staging environment
uv run python scripts/model_registry.py --env=staging

# Register models in production environment
uv run python scripts/model_registry.py --env=prod
```

#### Fire CLI Features

Python Fire automatically provides several convenient features:

```bash
# Show help for any script
uv run python scripts/predict.py --help
uv run python scripts/model_registry.py --help

# Show help for specific function
uv run python scripts/predict.py -- --help

# Use either --flag=value or --flag value syntax
uv run python scripts/predict.py --env dev  # Both syntaxes work
uv run python scripts/predict.py --env=dev
```

#### When to Use CLI vs API

**Use CLI scripts when**:
- Testing locally during development
- Running one-off predictions or model registry updates
- Debugging prediction pipelines with verbose logging
- You have local GCP credentials configured (`gcloud auth application-default login`)
- You want to iterate quickly without deploying to Cloud Run

**Use API endpoints when**:
- Running in production (Cloud Run Service)
- Automating via HTTP requests from other services
- Integrating with external systems
- You want centralized logging and monitoring
- You need authentication and access control

## Naming Conventions

### GCP Resources (per environment)
- **Cloud Run Service**: `mlsys-{env}` (e.g., `mlsys-dev`)
- **Artifact Registry**: `mlsys-{env}`
- **GCS Bucket**: `mlsys-models-{env}`
- **BigQuery Dataset**: `mlsys_{env}` (note: underscore, not hyphen)
- **Service Account**: `mlsys-sa-{env}@<your-gcp-project-id>.iam.gserviceaccount.com`

### Model Artifacts in GCS
- **Path pattern**: `gs://mlsys-models-{env}/{model-name}/{version}/model.pkl`
- **Model name**: lowercase, hyphen-separated (e.g., `titanic-survival`)
- **Version**: `v1`, `v2`, `v3`, etc. (semantic versioning)
- **Example**: `gs://mlsys-models-dev/titanic-survival/v1/model.pkl`
- **Optional metadata**: `gs://mlsys-models-dev/titanic-survival/v1/metadata.json`

### BigQuery Tables
- **Model Registry**: `<your-gcp-project-id>.mlsys_{env}.model_registry`
- **User tables**: Managed by data engineering team, full paths passed explicitly to endpoints

## GCP Resources

### Environments
All resources exist in the same GCP project (`<your-gcp-project-id>`) but are suffixed by environment:

**dev**: Automatic deployment on PR push (opened, synchronize, reopened)
- GCS bucket: `mlsys-models-dev`
- Cloud Run Service: `mlsys-dev`
- BigQuery dataset: `mlsys_dev`
- Service account: `mlsys-sa-dev@<your-gcp-project-id>.iam.gserviceaccount.com`

**staging**: Manual deployment for pre-production testing
- GCS bucket: `mlsys-models-staging`
- Cloud Run Service: `mlsys-staging`
- BigQuery dataset: `mlsys_staging`
- Service account: `mlsys-sa-staging@<your-gcp-project-id>.iam.gserviceaccount.com`

**prod**: Manual deployment with confirmation
- GCS bucket: `mlsys-models-prod`
- Cloud Run Service: `mlsys-prod`
- BigQuery dataset: `mlsys_prod`
- Service account: `mlsys-sa-prod@<your-gcp-project-id>.iam.gserviceaccount.com`

### Environment Variables
See `.env.example` for comprehensive template. Key variables:
```bash
# GCP Configuration (set via GitHub secrets/variables - NOT committed)
GCP_PROJECT_ID=<your-gcp-project>
GCP_REGION=<your-gcp-region>

# GCS Model Buckets (defaults provided in settings.py)
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

## Code Style and Patterns

### Python Code Style
- **Line length**: 100 characters
- **Target version**: Python 3.12
- **Linter/Formatter**: Ruff
- **Import sorting**: isort (via Ruff)
- **Type hints**: Encouraged but not enforced

### Ruff Configuration
Linting rules enabled:
- `E`: pycodestyle errors
- `W`: pycodestyle warnings
- `F`: pyflakes
- `I`: isort
- `B`: flake8-bugbear
- `C4`: flake8-comprehensions
- `UP`: pyupgrade

### Commit Message Style
- Use imperative mood ("Add feature" not "Added feature")
- Keep first line concise (< 72 characters)
- Do not mention AI assistance in commit messages
- Examples:
  - "Add BigQuery I/O utilities"
  - "Fix authentication in GCS upload"
  - "Update Dockerfile for Cloud Run optimization"

### Pre-commit Hooks Configuration
**File hygiene**: trailing-whitespace, end-of-file-fixer, mixed-line-ending

**Validation**: check-yaml, check-toml, check-json, check-added-large-files, check-merge-conflict

**Python**: ruff (lint + format)

**Security**: detect-secrets
- Use `# pragma: allowlist secret` for false positives
- No baseline file used

**Notebooks**: nbqa-ruff, nbstripout
- Preserve outputs, strip metadata
- Apply ruff to notebook code cells

## Key Components

### `api/main.py` - FastAPI Service
HTTP service with three endpoints:
- **`GET /predict`**: Run predictions on BigQuery data
  - Query params: `env`, `input_table`, `output_table`, `model_name`, `model_version`
  - Invokes `scripts/predict.py`
- **`GET /model-registry`**: Scan GCS and register models
  - Query params: `env`
  - Invokes `scripts/model_registry.py`
- **`GET /health`**: Health check for Cloud Run

### `scripts/predict.py` - Prediction Pipeline
Core prediction pipeline (invoked by `/predict` endpoint):
1. Pull data from BigQuery (using `bq_get()`)
2. Load model from GCS (using `gcs_get_pickle()`)
3. Make predictions with `.predict()` and `.predict_proba()`
4. Add metadata columns: `PredictionTimestamp`, `ModelName`, `ModelVersion`, `PredictionProbability`
5. Push predictions to BigQuery (using `bq_put()` with `WRITE_APPEND`)

**Note**: Currently hardcoded for Titanic model (expects `PassengerId`, produces `Survived` with prediction probability). See `scripts/predict.py:80-86` for implementation details. Needs generalization for other models.

### `scripts/model_registry.py` - Model Registration
Scans GCS bucket and registers models in BigQuery (invoked by `/model-registry` endpoint):
- Lists all blobs in `mlsys-models-{env}` bucket
- Filters for `.pkl` files matching pattern: `{model_name}/v{version}/model.pkl`
- Optionally reads `metadata.json` from same directory
- Upserts to `mlsys_{env}.model_registry` table with: model name, version, environment, bucket, file size, timestamps

## Infrastructure Details

### Terraform Structure
- **State**: Separate GCS buckets per environment (`mlsys-terraform-state-dev`, `mlsys-terraform-state-staging`, `mlsys-terraform-state-prod`)
- **Version**: Terraform 1.10.0 (managed via `.terraform-version` file)
- **Secrets**: Managed manually via `gcloud secrets` (NOT in Terraform)
- **Variables**: Local dev uses `terraform.tfvars`, CI/CD uses command-line variables
- **Modules**: Reusable module in `infra/modules/mlsys/`, instantiated per environment in `infra/envs/{env}/`

Key resources managed by Terraform:
- **GCS buckets** (`mlsys-models-{env}`) - Model artifact storage with versioning
- **BigQuery datasets** (`mlsys_{env}`) and model registry table
- **Artifact Registry repositories** (`mlsys-{env}`) - Docker images
- **Cloud Run Service** (`mlsys-{env}`) - FastAPI container
  - Note: Terraform ignores `image` changes (managed by CI/CD)
- **Service accounts** (`mlsys-sa-{env}`) with IAM roles:
  - `roles/bigquery.dataEditor` - Read/write BigQuery
  - `roles/bigquery.jobUser` - Run queries
  - `roles/storage.objectAdmin` - Full GCS access

### Docker Configuration
Multi-stage build optimized for Cloud Run:

**Builder stage**: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
- Uses uv for fast dependency installation (10-100x faster than pip)
- `UV_PYTHON_DOWNLOADS=0`: Force use of system Python 3.12 (no downloads)
- `UV_COMPILE_BYTECODE=1`: Pre-compile bytecode for faster container startup
- Install dependencies first (better layer caching, only rebuilds if `uv.lock` changes)
- Then install project code

**Runtime stage**: `python:3.12-slim-bookworm`
- Minimal runtime image (~150MB vs 1GB+ with builder)
- Copy only `.venv/`, `src/`, `scripts/`, `api/` from builder
- Expose port 8080 (Cloud Run standard)
- Default CMD: `uvicorn api.main:app --host 0.0.0.0 --port 8080`

**.dockerignore**: Excludes notebooks, tests, docs, infra, `.git`, IDE files for smaller build context

## CI/CD Architecture

### GitHub Actions Workflows

The project uses three CI/CD workflows for progressive deployment:

#### 1. PR Workflow (`.github/workflows/pr.yml`)
Unified workflow that auto-deploys to dev on PR events (opened, synchronize, reopened) targeting main:

**Steps**:
1. **Authorize**: Block external PRs (security check)
2. **Analyze Changes**: Detect code vs. infrastructure changes
3. **Pre-commit Checks**: Run all quality hooks (ruff, detect-secrets, nbstripout, etc.)
4. **Pytest**: Run all tests
5. **Terraform Checks**: Format, validate, plan for all environments
6. **Conditional Deployment to dev**:
   - If infra changed: Apply Terraform to dev
   - If code changed: Build Docker image with commit SHA tag, push to Artifact Registry, deploy to Cloud Run dev

**Smart Change Detection** - Avoids unnecessary operations by detecting what changed:

**Infrastructure changes** (triggers Terraform apply):
```yaml
infra/**
```

**Code changes** (triggers Docker build + deploy):
```yaml
src/**
api/**
scripts/**
pyproject.toml
uv.lock
Dockerfile
```

If only docs/tests change, workflow skips both Terraform and Docker steps.

#### 2. Staging Workflow (`.github/workflows/staging.yml`)
Deploys to staging via manual trigger only (must be triggered from main branch):

**Trigger**:
- Manual only via `workflow_dispatch` (GitHub Actions UI)
- Must be triggered from `main` branch after merging changes

**Steps**:
1. **Extract Versions**: Get mlsys version from `pyproject.toml` and Terraform version from `.terraform-version`
2. **Terraform**: Plan and apply for staging environment
3. **Build & Deploy**: Build Docker with version-based tags, push to Artifact Registry, deploy to Cloud Run staging

**Docker Image Tags**:
- `mlsys-staging:{version}` (e.g., `mlsys-staging:0.2.0`)
- `mlsys-staging:latest`

**No Change Detection**: Always runs both Terraform and build/deploy when triggered

**How to trigger**: Go to Actions → "Staging Deployment" → Run workflow → Select branch: **main**

#### 3. Production Workflow (`.github/workflows/prod.yml`)
Deploys to production via manual trigger only (must be triggered from main branch):

**Trigger**:
- Manual only via `workflow_dispatch` (GitHub Actions UI)
- Must be triggered from `main` branch after merging changes

**Steps**:
1. **Extract Versions**: Get mlsys version from `pyproject.toml` and Terraform version from `.terraform-version`
2. **Terraform**: Plan and apply for production environment
3. **Build & Deploy**: Build Docker with version-based tags, push to Artifact Registry, deploy to Cloud Run production

**Docker Image Tags**:
- `mlsys-prod:{version}` (e.g., `mlsys-prod:0.2.0`)
- `mlsys-prod:latest`

**No Change Detection**: Always runs both Terraform and build/deploy when triggered

**How to trigger**: Go to Actions → "Production Deployment" → Run workflow → Select branch: **main**

### GitHub Secrets and Variables
**Environment**: `gcp` (single environment for all deployments)
- **Secret**: `GCP_SA_KEY` - GCP service account JSON key for `mlsys-github-actions@<your-gcp-project-id>.iam.gserviceaccount.com`  # pragma: allowlist secret
- **Variables**:
  - `GCP_PROJECT_ID` = `<your-gcp-project-id>`
  - `GCP_REGION` = `<your-gcp-region>`

## Model Versioning

- **Versioning scheme**: Semantic versioning (v1, v2, v3, etc.)
- **Storage**: GCS folder structure `gs://mlsys-models-{env}/{model-name}/v{N}/model.pkl`
- **Version propagation**: Passed as query parameter to `/predict` endpoint
- **Registry**: `/model-registry` endpoint scans GCS and tracks all versions in BigQuery `mlsys_{env}.model_registry` table

## Best Practices

### BigQuery I/O
- Always pass full table paths explicitly: `project.dataset.table`
- Use `bq_get(query: str) -> pd.DataFrame` for reads
  - Executes SQL query and returns results as DataFrame
  - Example: `df = bq_get("SELECT * FROM project.dataset.table LIMIT 10")`
- Use `bq_put(df: pd.DataFrame, table_id: str, write_disposition: str = "WRITE_APPEND")` for writes
  - Write dispositions: `WRITE_APPEND`, `WRITE_TRUNCATE`, `WRITE_EMPTY`
  - Example: `bq_put(df, "project.dataset.table", "WRITE_TRUNCATE")`
- Data engineering team manages table schemas and lifecycle

### GCS I/O
- Model artifacts stored in versioned folders: `{model-name}/v{N}/model.pkl`
- Use `gcs_get_pickle(bucket_name: str, blob_path: str) -> Any` for downloading pickled models
  - Downloads and deserializes pickled objects
  - Example: `model = gcs_get_pickle("mlsys-models-dev", "titanic-survival/v1/model.pkl")`
- Use `gcs_put_pickle(obj: Any, bucket_name: str, blob_path: str)` for uploading pickled models
  - Serializes and uploads objects using joblib
  - Example: `gcs_put_pickle(model, "mlsys-models-dev", "titanic-survival/v1/model.pkl")`
- Use `gcs_get(bucket_name: str, blob_path: str) -> bytes` for raw bytes (e.g., `metadata.json`)
- Use `gcs_put(content: bytes | str, bucket_name: str, blob_path: str)` for uploading raw bytes/strings
- Use `gcs_list_blobs(bucket_name: str) -> list[Blob]` to list all objects
- Bucket names vary by environment: `mlsys-models-{env}`

### Notebook Development
- Use notebooks for EDA and model experimentation only
- Keep production code in `src/mlsys/`, `api/`, and `scripts/`
- nbstripout automatically strips metadata but preserves outputs (configured in `.pre-commit-config.yaml`)
- Follow notebook naming convention: `{model-name}-{purpose}.ipynb` (see `notebooks/README.md`)
- See `notebooks/titanic-survival-example.ipynb` for complete example workflow

### Testing
- Run unit and integration tests before committing: `uv run pytest`
- Pre-commit hooks run automatically on commit
- Manual hook execution: `uv run pre-commit run --all-files`
- Test in dev environment before promoting to staging
- Always validate in staging before production deployment
- See detailed testing documentation in the "Testing" section below

## Testing

### Test Structure

The project uses pytest with two types of tests:

**Unit Tests** (`tests/unit/`, 36 tests):
- Test individual functions in isolation
- Fast execution (< 1 second total)
- Mock all external services (BigQuery, GCS)
- Located in: `tests/unit/test_bq.py`, `tests/unit/test_gcs.py`, `tests/unit/test_predict.py`, `tests/unit/test_model_registry.py`
- Marker: `@pytest.mark.unit`

**Integration Tests** (`tests/integration/`, 16 tests):
- Test how components work together
- Verify FastAPI endpoints route to correct scripts
- Ensure HTTP request/response contracts are correct
- Located in: `tests/integration/test_api.py`
- Marker: `@pytest.mark.integration`

### Running Tests

```bash
# Run all tests with coverage report
uv run pytest

# Run only unit tests (fast)
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run without coverage (faster, easier debugging)
uv run pytest --no-cov

# Run with verbose output
uv run pytest -vv

# Run specific test file
uv run pytest tests/unit/test_bq.py -v

# Run specific test function
uv run pytest tests/unit/test_bq.py::TestBqGet::test_bq_get_success -v

# Show full traceback
uv run pytest --tb=long
```

### Coverage Reports

After running tests, view the HTML coverage report:

```bash
# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

The coverage report shows:
- Line-by-line code coverage with visual highlights
- Percentage coverage per file
- Untested code paths highlighted in red
- Note: `vis.py` is excluded (not deployed to production)

### Fixtures and Mocks (`tests/conftest.py`)

**Fixtures** provide reusable test data:
- `sample_titanic_df`: Sample DataFrame for prediction tests
- `sample_predictions`: Mock prediction results
- `sample_prediction_probabilities`: Mock prediction probabilities
- `mock_sklearn_model`: Serializable mock scikit-learn model
- `pickled_model_bytes`: Serialized model for GCS tests
- `mock_gcs_blob_list`: Mock GCS blobs for model registry tests

**Mocks** simulate external services:
- `mock_bq_client`: Mock BigQuery client (no API calls)
- `mock_gcs_client`: Mock GCS client (no API calls)
- `mock_settings`: Mock environment variables

**Benefits**:
- Consistent test data across all tests
- No GCP credentials required for testing
- Fast test execution (no network I/O)
- Predictable results (no external dependencies)

### Why We Test This Way

**Unit Tests**:
- Verify business logic correctness in isolation
- Ensure functions handle edge cases properly
- Test error handling and validation
- Example: Test that `bq_put()` calls BigQuery API with correct parameters

**Integration Tests**:
- Verify components work together correctly
- Test API endpoint routing and parameter validation
- Ensure HTTP contracts are maintained
- Example: Test that `/predict` endpoint validates query parameters and calls `predict()` function

**Mocking Strategy**:
- Mock BigQuery and GCS clients to avoid real API calls
- Use `unittest.mock.patch` to replace clients during tests
- Mock returns pre-defined data instead of querying actual services
- Example: Mock BigQuery client returns pre-defined DataFrame instead of querying BigQuery

### Test Coverage Goals

- **Target**: 100% coverage of production code
- **Current**: See coverage report with `open htmlcov/index.html`
- **Excluded**: `vis.py` (not deployed to production), test files
- **Priority**: All code in `src/mlsys/`, `api/`, and `scripts/` must be tested

### Writing New Tests

When adding new features, follow these patterns:

**1. Add fixtures to `conftest.py` if needed**:
```python
@pytest.fixture
def sample_new_data():
    """Sample data for new feature."""
    return pd.DataFrame({"col1": [1, 2, 3]})
```

**2. Write unit tests for new functions**:
```python
@pytest.mark.unit
def test_new_function(mock_bq_client):
    """Test new function with mocked dependencies."""
    result = new_function(mock_bq_client)
    assert result == expected_value
```

**3. Write integration tests for new endpoints**:
```python
@pytest.mark.integration
def test_new_endpoint(client):
    """Test new API endpoint."""
    response = client.get("/new-endpoint?param=value")
    assert response.status_code == 200
```

**4. Use mocks for external services**:
```python
from unittest.mock import patch

@pytest.mark.unit
def test_with_mock():
    with patch("mlsys.bq.bigquery.Client") as mock_client:
        mock_client.return_value = mock_bq_client
        result = function_that_uses_bq()
        assert result == expected
```

## Common Workflows

### Adding a New Model
1. **Develop in Jupyter**: Create notebook in `notebooks/{model-name}-{purpose}.ipynb`
2. **Train model**: Use `bq_get()` to fetch training data, train with scikit-learn
3. **Upload to GCS**: Use `gcs_put_pickle(model, GCS_BUCKET_MODELS_DEV, "{model-name}/v1/model.pkl")`
4. **Register model**: Call `/model-registry?env=dev` endpoint to scan and register
5. **Test predictions**: Call `/predict?env=dev&input_table=...&output_table=...&model_name={model-name}&model_version=v1`
6. **Promote**: Upload to staging/prod buckets and repeat registration/testing

**Note**: Current `/predict` endpoint is hardcoded for Titanic model. Generalization needed for other models.

### Deploying Infrastructure Changes
1. **Make changes** in `infra/` directory (e.g., add BigQuery table, modify IAM)
2. **Create PR** - triggers Terraform format, validate, and plan for all environments
3. **Review plan** in PR checks (GitHub Actions summary)
4. **PR push** - auto-applies Terraform changes to dev environment on PR opened/synchronize/reopened
5. **Merge to main** - changes are now in main branch, ready for staging/prod deployment
6. **Deploy to staging** - Manually trigger: Go to Actions → "Staging Deployment" → Run workflow on main branch
7. **Test in staging** - Verify changes work correctly in staging environment
8. **Deploy to production** - Manually trigger: Go to Actions → "Production Deployment" → Run workflow on main branch

**Important**: Always deploy to staging first and test before deploying to production.

### Updating Dependencies
```bash
uv add <package-name>       # Add new dependency
uv sync                     # Sync environment
git add pyproject.toml uv.lock
git commit -m "Add <package-name> dependency"
```

### Versioning and Release Management
The project uses semantic versioning defined in `pyproject.toml`. This version is used for Docker image tags in staging and production deployments.

**When to bump the version**:
- **Patch** (e.g., `0.2.0` → `0.2.1`): Bug fixes, minor updates
- **Minor** (e.g., `0.2.0` → `0.3.0`): New features, backward-compatible changes
- **Major** (e.g., `0.2.0` → `1.0.0`): Breaking changes, major refactoring

**How to bump the version**:
```bash
# 1. Update version in pyproject.toml
# Change: version = "0.2.0" to version = "0.3.0"

# 2. Commit the version bump
git add pyproject.toml
git commit -m "Bump version to 0.3.0"

# 3. Merge to main (triggers staging/prod deployments with new version tags)
# Docker images will be tagged as:
#   - mlsys-staging:0.3.0
#   - mlsys-prod:0.3.0
```

**Best practice**: Bump the version before merging to main if the changes warrant a new release to staging/prod.

## Troubleshooting

### Pre-commit Hook Failures
- **detect-secrets**: Add `# pragma: allowlist secret` for false positives
- **ruff**: Check error message, fix code or add `# noqa: <code>` if intentional
- **nbstripout**: Ensure notebooks are in proper format
- **check-yaml/toml/json**: Validate file syntax

### UV Package Issues
- Clear cache: `uv cache clean`
- Regenerate lockfile: `rm uv.lock && uv sync`
- Ensure Python 3.12 is active

### Docker Build Issues
- Verify Python version consistency (pyproject.toml, Dockerfile builder, Dockerfile runtime)
- Check layer caching: dependencies should install before code copy
- Validate `UV_PYTHON_DOWNLOADS=0` and `UV_COMPILE_BYTECODE=1` are set

### Terraform Issues
- Verify correct state bucket for environment
- Check `.terraform-version` matches CI/CD
- Ensure GCP credentials are properly configured
- Review Terraform plan before apply

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

# Clear pytest cache
rm -rf .pytest_cache __pycache__ tests/__pycache__
```

**Common issues**:
- **Import errors**: Ensure `uv sync --group test` was run
- **Fixture not found**: Check `conftest.py` for fixture definitions
- **Mock not working**: Verify patch path matches actual import path
- **Coverage too low**: Run `open htmlcov/index.html` to see uncovered lines

## API Usage Examples

### Making Predictions
```bash
# Dev environment
curl "https://mlsys-dev-xxxxxx.run.app/predict?env=dev&input_table=<your-gcp-project-id>.titanic.test&output_table=<your-gcp-project-id>.titanic.predictions&model_name=titanic-survival&model_version=v1"

# Prod environment
curl "https://mlsys-prod-xxxxxx.run.app/predict?env=prod&input_table=<your-gcp-project-id>.titanic.test&output_table=<your-gcp-project-id>.titanic.predictions&model_name=titanic-survival&model_version=v1"
```

### Registering Models
```bash
# Scan dev bucket and register all models
curl "https://mlsys-dev-xxxxxx.run.app/model-registry?env=dev"

# Scan prod bucket
curl "https://mlsys-prod-xxxxxx.run.app/model-registry?env=prod"
```

### Health Check
```bash
curl "https://mlsys-dev-xxxxxx.run.app/health"
```
