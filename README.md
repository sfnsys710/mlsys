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

# Launch Jupyter for notebook development
uv run jupyter lab
```

## Project Structure

```
mlsys/
├── src/mlsys/          # Main Python package
│   ├── bq.py           # BigQuery I/O utilities
│   ├── gcs.py          # GCS I/O utilities
│   ├── vis.py          # Visualization helpers
│   └── settings.py     # Configuration management
├── dags/               # Airflow DAGs
├── notebooks/          # Jupyter notebooks for analysis
├── scripts/            # Deployment and prediction scripts
├── infra/              # Terraform infrastructure
└── .github/            # CI/CD workflows
```

## Notebook Development

Notebooks in `notebooks/` are used for exploratory data analysis and model development:

### Workflow
1. **Download Data**: Use `bq_get()` to fetch data from BigQuery
2. **Explore**: Perform EDA, visualizations, feature engineering
3. **Train Models**: Experiment with algorithms and hyperparameters
4. **Evaluate**: Assess model performance
5. **Upload Model**: Use `gcs_put()` to save model artifacts to GCS

### Example
```python
from mlsys.bq import bq_get
from mlsys.gcs import gcs_put
from mlsys.settings import GCS_BUCKET_MODELS_DEV

# Download data
df = bq_get("SELECT * FROM project.dataset.training_data")

# Train model
model.fit(X_train, y_train)

# Upload to GCS
gcs_put(model, GCS_BUCKET_MODELS_DEV, "my-model/v1/model.pkl")
```

See `notebooks/README.md` for detailed guidance and `notebooks/titanic-survival-example.ipynb` for a complete example.

## Documentation

- [notebooks/README.md](./notebooks/README.md) - Notebook development guide
- [CLAUDE.md](./CLAUDE.md) - AI assistant guidance

## Environments

- **dev**: Automatic deployment on PR to main
- **staging**: Manual deployment for pre-production testing
- **prod**: Manual deployment with confirmation

## Status

✅ **Phase 1-5**: Foundation, Core Utilities, Containerization, Core Scripts
✅ **PR #10**: Model Registry Cloud Function
✅ **PR #11**: Terraform Infrastructure (modular architecture)
✅ **PR #13-15**: CI/CD Workflows (merged, with smart change detection)
🚧 **PR #17**: Application Layer - Notebooks (in progress)
