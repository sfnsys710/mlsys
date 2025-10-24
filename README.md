# mlsys

ML System for training models in Jupyter and deploying to GCP with scheduled predictions using Cloud Scheduler and Cloud Run Jobs.

## Overview

Repository for machine learning development and production deployment with progressive deployment strategy across dev, staging, and prod environments.

**Architecture**: Develop models in Jupyter notebooks, deploy predictions as Cloud Run Jobs, and schedule them with Cloud Scheduler.

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
├── notebooks/          # Jupyter notebooks for model development
├── cloud_runs/         # Cloud Run Jobs (packaged in Docker)
│   └── predict.py      # Prediction pipeline script
├── cloud_funcs/        # Cloud Functions (deployed separately)
│   └── model_registry/ # Model registration on GCS upload
├── infra/              # Terraform infrastructure
└── .github/            # CI/CD workflows
```

## Architecture

### Local Development
1. Download data from BigQuery using `bq_get()`
2. Perform EDA and train models in Jupyter notebooks
3. Upload model artifacts to GCS using `gcs_put()`

### GCP Production
- **Cloud Scheduler**: Triggers predictions on a schedule (daily, hourly, etc.)
- **Cloud Run Jobs**: Executes prediction pipeline (pull data → predict → save results)
- **Cloud Functions**: Registers model metadata when artifacts are uploaded to GCS
- **BigQuery**: Stores training data, predictions, and model registry
- **GCS**: Stores model artifacts with versioning (v1, v2, etc.)

### Deployment Flow
```
Jupyter → GCS → Model Registry (Cloud Function) → BigQuery
                                ↓
                        Cloud Scheduler → Cloud Run Job → BigQuery Predictions
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

✅ **Complete**: Project setup finished with all core components
- Foundation: Package structure, pre-commit hooks, settings
- Core utilities: BigQuery, GCS, visualization helpers
- Infrastructure: Terraform modules for all environments
- CI/CD: Docker builds, Terraform deployments
- Application layer: Jupyter notebooks with Titanic example
- Model registry: Cloud Function for automatic registration
- Architecture: Cloud Scheduler + Cloud Run Jobs (simplified from Airflow)
