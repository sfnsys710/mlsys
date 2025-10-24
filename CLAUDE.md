# CLAUDE.md - AI Assistant Guidance

This document provides comprehensive guidance for AI assistants working on the mlsys repository.

## Project Overview

**Purpose**: ML system for training models in Jupyter notebooks and deploying to GCP with scheduled predictions.

**Key Technologies**:
- Python 3.12 with uv package manager
- GCP: BigQuery, GCS, Cloud Run, Airflow Composer, Artifact Registry
- Infrastructure: Terraform
- CI/CD: GitHub Actions
- Containerization: Docker (multi-stage builds)

**GCP Project**: `soufianesys` (single project, resources suffixed with `-dev`, `-staging`, `-prod`)

## Architecture

### Local Workflow
1. Download data from BigQuery using utility functions
2. Perform EDA and ML model selection in Jupyter notebooks
3. Upload trained model artifacts to GCS

### GCP Workflow
- **Environments**: dev, staging, and prod (same GCP project, different resources)
- **Orchestration**: Airflow Composer with model-specific DAGs
- **Compute**: Cloud Run jobs running Docker containers
- **CI/CD**: GitHub Actions with progressive deployment
- **Data**: BigQuery tables managed by data engineering team (full table paths passed explicitly)

### Progressive Deployment Strategy
```
dev (automatic on PR) → staging (manual) → prod (manual with confirmation)
```

## Repository Structure

```
mlsys/
├── .github/
│   └── workflows/           # CI/CD workflows
├── src/mlsys/               # Main Python package (managed by uv)
│   ├── bq.py                # BigQuery I/O (bq_get, bq_put)
│   ├── gcs.py               # GCS I/O (gcs_get, gcs_put)
│   ├── vis.py               # Visualization helpers
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

For each model (e.g., titanic-survival):
- **DAG Name**: `titanic-survival-{env}` (e.g., `titanic-survival-dev`, `titanic-survival-staging`, `titanic-survival-prod`)
- **GCS Path**: `gs://ml-models-{env}/titanic-survival/v1/`, `gs://ml-models-{env}/titanic-survival/v2/`, etc.
- **CI/CD Job**: `deploy-titanic-survival-{env}`
- **Service Account**: `titanic-survival-dag-sa-{env}@soufianesys.iam.gserviceaccount.com`
- **BigQuery Tables**: Managed by data engineering team, full paths passed explicitly (e.g., `project.dataset.table`)

## GCP Resources

### Environments
All resources exist in the same GCP project (`soufianesys`) but are suffixed by environment:

**dev**: Automatic deployment on PR to main
- GCS bucket: `ml-models-dev`
- Composer bucket: `<composer-bucket-dev>`
- Service accounts: `*-dag-sa-dev@soufianesys.iam.gserviceaccount.com`

**staging**: Manual deployment for pre-production testing
- GCS bucket: `ml-models-staging`
- Composer bucket: `<composer-bucket-staging>`
- Service accounts: `*-dag-sa-staging@soufianesys.iam.gserviceaccount.com`

**prod**: Manual deployment with confirmation
- GCS bucket: `ml-models-prod`
- Composer bucket: `<composer-bucket-prod>`
- Service accounts: `*-dag-sa-prod@soufianesys.iam.gserviceaccount.com`

### Environment Variables
See `.env.example` for comprehensive template. Key variables:
```bash
# GCP Configuration (set via GitHub secrets/variables - NOT committed)
GCP_PROJECT_ID=<your-gcp-project>
GCP_REGION=<your-gcp-region>

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

## Key Scripts

### `scripts/predict.py` - `pull_predict_push()`
Core prediction pipeline that runs in Cloud Run jobs:
1. Pull data from BigQuery (using `bq_get()`)
2. Pull model artifacts from GCS (using `gcs_get()`)
3. Make predictions using loaded model
4. Add metadata (timestamp, model name, model version)
5. Push predictions back to BigQuery (using `bq_put()`)

### `scripts/model_registry/` - Cloud Function
Event-based trigger on new object uploads to `ml-models-{dev/staging/prod}` buckets:
- Registers model metadata in registry
- Updates model inventory
- Tracks: model name, version, upload timestamp, file size, uploader, environment
- Stored in BigQuery table: `ml_registry.models`

## Infrastructure Details

### Terraform Structure
- **State**: Separate GCS buckets per environment (`sfn-terraform-state-dev`, `sfn-terraform-state-staging`, `sfn-terraform-state-prod`)
- **Version**: Managed via `.terraform-version` file
- **Secrets**: Managed manually via `gcloud secrets` (NOT in Terraform)
- **Variables**: Local dev uses `terraform.tfvars`, CI/CD uses command-line variables
- **Modules**: Reusable module for service account creation

Key resources:
- GCS buckets (`ml-models-{env}`)
- Artifact Registry repositories
- Service accounts with IAM roles
- Cloud Run jobs (via Docker images)

### Docker Configuration
Multi-stage build following best practices:

**Builder stage**: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
- `UV_PYTHON_DOWNLOADS=0`: Force use of system Python 3.12
- `UV_COMPILE_BYTECODE=1`: Pre-compile bytecode for faster startup
- Install dependencies first for better layer caching

**Runtime stage**: `python:3.12-slim-bookworm`
- Minimal runtime image
- Copy only necessary files from builder
- Optimized for Cloud Run

## CI/CD Architecture

### Workflow Design
Three-tier modular architecture:

**Main Workflows** (trigger deployments):
- `pr.yml`: Auto-deploy to dev on PR to main
- `staging.yml`: Manual staging deployment
- `prod.yml`: Manual prod deployment with confirmation
- `deploy-dag.yml`: Manual DAG deployment

**Reusable Components**:
- `terraform-workflow.yml`: Parameterized Terraform operations
- `docker-build.yml`: Parameterized Docker build/push

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

### GitHub Secrets and Variables
**Environment**: `gcp` (single environment for all deployments)
- Secret: `SA` (GCP service account JSON key) <!-- pragma: allowlist secret -->
- Variables: `GCP_PROJECT_ID`, `GCP_REGION`

## Model Versioning

- **Versioning scheme**: Semantic versioning (v1, v2, v3, etc.)
- **Storage**: GCS folder structure `gs://ml-models-{env}/{model-name}/v{N}/`
- **Version propagation**: Passed to prediction script via DAG environment variables
- **Registry**: Cloud Function tracks all versions in BigQuery

## Best Practices

### BigQuery I/O
- Always pass full table paths explicitly: `project.dataset.table`
- Use `bq_get(query)` for reads (returns DataFrame)
- Use `bq_put(df, table_id, write_disposition)` for writes
- Data engineering team manages table schemas and lifecycle

### GCS I/O
- Model artifacts stored in versioned folders
- Use `gcs_get(bucket_name, blob_path)` for downloads
- Use `gcs_put(obj, bucket_name, blob_path)` for uploads
- Bucket names vary by environment: `ml-models-{env}`

### Notebook Development
- Use notebooks for EDA and model experimentation only
- Keep production code in `src/mlsys/` and `scripts/`
- Use nbstripout to avoid committing metadata
- Follow notebook naming convention (see `notebooks/README.md`)

### Testing
- Pre-commit hooks run automatically on commit
- Manual hook execution: `uv run pre-commit run --all-files`
- Test in dev environment before promoting to staging
- Always validate in staging before production deployment

## Common Workflows

### Adding a New Model
1. Create Jupyter notebook for model development
2. Train and evaluate model using latest data from BigQuery
3. Upload model artifacts to GCS: `gs://ml-models-dev/{model-name}/v1/`
4. Create Airflow DAG in `dags/{model_name}_dag.py`
5. Add Terraform service account in `infra/service_accounts.tf`
6. Update CI/CD workflows if needed
7. Test in dev environment
8. Promote to staging, then prod

### Deploying Infrastructure Changes
1. Make changes in `infra/` directory
2. Create PR (triggers Terraform plan for dev)
3. Review plan in PR checks
4. Merge to main (auto-applies to dev)
5. Manually trigger staging workflow
6. Review staging, then manually trigger prod workflow

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

## References

- [PROJECT_PLAN.md](./PROJECT_PLAN.md) - Detailed implementation plan with 17 PRs
- [README.md](./README.md) - Project overview and quick start
- [pyproject.toml](./pyproject.toml) - Package configuration
- [.pre-commit-config.yaml](./.pre-commit-config.yaml) - Code quality hooks
