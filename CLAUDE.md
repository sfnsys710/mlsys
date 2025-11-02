# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Purpose**: ML system for training models in Jupyter notebooks and deploying to GCP with an HTTP prediction service.

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
dev (automatic on PR merge) → staging (manual) → prod (manual with confirmation)
```

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
│   └── workflows/           # CI/CD workflows (pr.yml)
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

### Git Workflow
```bash
git checkout -b <branch-name>          # Create feature branch
git add .                              # Stage changes
git commit -m "message"                # Commit (triggers pre-commit hooks)
git push origin <branch-name>          # Push to remote
gh pr create --title "..." --body "..." # Create pull request
```

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

**dev**: Automatic deployment on PR merge to main
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
GCP_PROJECT_ID=<your-gcp-project-id>
GCP_REGION=<your-gcp-region>

# GCS Model Buckets (defaults provided in settings.py)
GCS_BUCKET_MODELS_DEV=mlsys-models-dev
GCS_BUCKET_MODELS_STAGING=mlsys-models-staging
GCS_BUCKET_MODELS_PROD=mlsys-models-prod

# Note: BigQuery table paths are passed explicitly to API endpoints
# Example: GET /predict?env=dev&input_table=project.dataset.input&...
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
4. Add metadata columns: `PredictionTimestamp`, `ModelName`, `ModelVersion`
5. Push predictions to BigQuery (using `bq_put()` with `WRITE_APPEND`)

**Note**: Currently hardcoded for Titanic model (expects `PassengerId`, produces `Survived`). Needs generalization for other models.

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

### GitHub Actions Workflow (`.github/workflows/pr.yml`)
Unified workflow that auto-deploys to dev on PR merge to main:

**Steps**:
1. **Authorize**: Block external PRs (security check)
2. **Analyze Changes**: Detect code vs. infrastructure changes
3. **Pre-commit Checks**: Run all quality hooks (ruff, detect-secrets, nbstripout, etc.)
4. **Terraform Operations**: Format, validate, plan for all environments
5. **Conditional Deployment**:
   - If infra changed: Apply Terraform to dev
   - If code changed: Build Docker image, push to Artifact Registry, deploy to Cloud Run dev

### Smart Change Detection
Avoids unnecessary operations by detecting what changed:

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
- Use `bq_get(query)` for reads (returns DataFrame)
- Use `bq_put(df, table_id, write_disposition)` for writes
- Data engineering team manages table schemas and lifecycle

### GCS I/O
- Model artifacts stored in versioned folders: `{model-name}/v{N}/model.pkl`
- Use `gcs_get_pickle(bucket_name, blob_path)` for downloading pickled models
- Use `gcs_put_pickle(obj, bucket_name, blob_path)` for uploading pickled models
- Use `gcs_get(bucket_name, blob_path)` for raw bytes (e.g., `metadata.json`)
- Use `gcs_put(bytes, bucket_name, blob_path)` for raw bytes
- Use `gcs_list_blobs(bucket_name)` to list all objects
- Bucket names vary by environment: `mlsys-models-{env}`

### Notebook Development
- Use notebooks for EDA and model experimentation only
- Keep production code in `src/mlsys/`, `api/`, and `scripts/`
- nbstripout automatically strips metadata but preserves outputs (configured in `.pre-commit-config.yaml`)
- Follow notebook naming convention: `{model-name}-{purpose}.ipynb` (see `notebooks/README.md`)
- See `notebooks/titanic-survival-example.ipynb` for complete example workflow

### Testing
- Pre-commit hooks run automatically on commit
- Manual hook execution: `uv run pre-commit run --all-files`
- Test in dev environment before promoting to staging
- Always validate in staging before production deployment

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
4. **Merge to main** - auto-applies Terraform changes to dev environment
5. **Manual promotion**: Manually run Terraform apply for staging, then prod (currently manual process)

### Updating Dependencies
```bash
uv add <package-name>       # Add new dependency
uv sync                     # Sync environment
git add pyproject.toml uv.lock
git commit -m "Add <package-name> dependency"
```

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

## References

- [README.md](./README.md) - Project overview, setup instructions, quick start
- [notebooks/README.md](./notebooks/README.md) - Comprehensive notebook development guide
- [notebooks/titanic-survival-example.ipynb](./notebooks/titanic-survival-example.ipynb) - Complete example workflow
- [pyproject.toml](./pyproject.toml) - Package configuration and dependencies
- [.pre-commit-config.yaml](./.pre-commit-config.yaml) - Code quality hooks configuration
- [.env.example](./.env.example) - Environment variable template
