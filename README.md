# mlsys

ML System for training models in Jupyter and deploying to GCP with scheduled predictions.

## Overview

Repository for machine learning development and production deployment with progressive deployment strategy across dev, staging, and prod environments.

## Quick Start

```bash
# Install dependencies
uv sync

# Run pre-commit hooks
uv run pre-commit install
uv run pre-commit run --all-files
```

## Project Structure

```
mlsys/
├── src/mlsys/          # Main Python package
│   ├── bq/             # BigQuery I/O utilities
│   ├── gcs/            # GCS I/O utilities
│   └── vis/            # Visualization helpers
├── dags/               # Airflow DAGs
├── notebooks/          # Jupyter notebooks for analysis
├── scripts/            # Deployment and prediction scripts
├── infra/              # Terraform infrastructure
└── .github/            # CI/CD workflows
```

## Documentation

- [PROJECT_PLAN.md](./PROJECT_PLAN.md) - Detailed implementation plan with 17 PRs
- [CLAUDE.md](./CLAUDE.md) - AI assistant guidance (coming soon)

## Environments

- **dev**: Automatic deployment on PR to main
- **staging**: Manual deployment for pre-production testing
- **prod**: Manual deployment with confirmation

## Status

🚧 Initial setup in progress - PR #1: Package structure complete
