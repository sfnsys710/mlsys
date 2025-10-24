# Notebooks

This directory contains Jupyter notebooks for exploratory data analysis (EDA) and ML model development.

## Quick Start

```bash
# Launch Jupyter Lab
uv run jupyter lab

# Notebooks will open in your browser at http://localhost:8888
```

## Development Workflow

Notebooks are used for **experimentation and model development only**. Production code lives in `src/mlsys/` and `scripts/`.

### Typical Workflow

1. **Download Data**: Use `bq_get()` to fetch data from BigQuery
2. **Explore**: Perform EDA, visualizations, feature engineering
3. **Train Models**: Experiment with different algorithms and hyperparameters
4. **Evaluate**: Assess model performance on validation/test sets
5. **Upload Model**: Use `gcs_put()` to save trained model to GCS

### Example

```python
from mlsys.bq import bq_get, bq_put
from mlsys.gcs import gcs_get, gcs_put
from mlsys.settings import GCS_BUCKET_MODELS_DEV
import joblib

# 1. Download data from BigQuery
df = bq_get("SELECT * FROM project.dataset.training_data")

# 2. Train model
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier()
model.fit(X_train, y_train)

# 3. Upload trained model to GCS
gcs_put(
    obj=model,
    bucket_name=GCS_BUCKET_MODELS_DEV,
    blob_path="my-model/v1/model.pkl"
)
```

## Naming Conventions

Follow this naming pattern for notebooks:

```
{model-name}-{purpose}.ipynb
```

**Examples**:
- `titanic-survival-example.ipynb` - Example notebook
- `churn-prediction-eda.ipynb` - Exploratory data analysis
- `churn-prediction-training.ipynb` - Model training
- `fraud-detection-feature-engineering.ipynb` - Feature engineering

**Guidelines**:
- Use lowercase with hyphens
- Start with model name
- End with purpose (eda, training, evaluation, etc.)
- Keep names concise and descriptive

## Using BigQuery

Always pass **fully qualified table paths** to `bq_get()` and `bq_put()`:

```python
# Good: Fully qualified table path
df = bq_get("SELECT * FROM my-project.my_dataset.my_table LIMIT 1000")

# Bad: Relative table path (will fail)
df = bq_get("SELECT * FROM my_table")
```

For writes, specify the full table ID:

```python
bq_put(
    df=predictions,
    table_id="my-project.my_dataset.predictions",
    write_disposition="WRITE_APPEND"
)
```

## Using GCS

Model artifacts are stored in versioned folders following this pattern:

```
gs://{bucket-name}/{model-name}/v{N}/model.pkl
```

**Bucket Names by Environment**:
- Dev: `ml-models-dev`
- Staging: `ml-models-staging`
- Prod: `ml-models-prod`

**Example**:

```python
from mlsys.gcs import gcs_put
from mlsys.settings import GCS_BUCKET_MODELS_DEV
import joblib

# Upload model artifact
gcs_put(
    obj=model,
    bucket_name=GCS_BUCKET_MODELS_DEV,
    blob_path="titanic-survival/v1/model.pkl"
)

# Upload additional artifacts (scaler, encoder, etc.)
gcs_put(
    obj=scaler,
    bucket_name=GCS_BUCKET_MODELS_DEV,
    blob_path="titanic-survival/v1/scaler.pkl"
)
```

## Model Versioning

- **Version scheme**: v1, v2, v3, etc. (semantic versioning)
- **GCS structure**: `gs://ml-models-{env}/{model-name}/v{N}/`
- **Artifact naming**: Use descriptive names (`model.pkl`, `scaler.pkl`, `encoder.pkl`)

When creating a new version:

```python
# Upload to new version folder
gcs_put(model, GCS_BUCKET_MODELS_DEV, "my-model/v2/model.pkl")
```

## Pre-commit Hooks

Notebooks are processed by pre-commit hooks on `git commit`:

1. **nbstripout**: Strips metadata but **preserves cell outputs**
2. **nbqa-ruff**: Applies ruff linting/formatting to code cells

To manually run hooks on all notebooks:

```bash
uv run pre-commit run --all-files
```

**Important**: Outputs are preserved so you can review results in PRs. However, keep notebooks clean and avoid committing notebooks with excessive output.

## Best Practices

### Code Organization
- Keep notebooks focused on one task (EDA, training, evaluation)
- Extract reusable functions to `src/mlsys/` modules
- Use relative imports: `from mlsys.bq import bq_get`

### Data Management
- Always download fresh data at the start of analysis
- Document data sources (BigQuery table paths)
- Include data validation checks

### Model Development
- Document model assumptions and decisions
- Include evaluation metrics and visualizations
- Track hyperparameters and configurations
- Save model versioning information

### Documentation
- Use markdown cells to explain your approach
- Include section headers for structure
- Document any manual steps or decisions

### Performance
- Use `LIMIT` clauses when prototyping queries
- Sample large datasets for initial exploration
- Only download full datasets when needed

## Visualization

Use the visualization helpers from `mlsys.vis`:

```python
from mlsys.vis import setup_plot_style

# Apply consistent styling
setup_plot_style()

# Your plotting code
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
# ...
```

## Environment Variables

Notebooks have access to all environment variables from `.env`:

```python
from mlsys.settings import GCP_PROJECT_ID, GCP_REGION, GCS_BUCKET_MODELS_DEV

print(f"Project: {GCP_PROJECT_ID}")
print(f"Dev bucket: {GCS_BUCKET_MODELS_DEV}")
```

For local development, copy `.env.example` to `.env` and fill in your values.

## Example Notebooks

- `titanic-survival-example.ipynb` - Complete end-to-end example demonstrating:
  - Data loading and exploration
  - Model training and evaluation
  - Uploading artifacts to GCS
  - Following best practices

## Troubleshooting

### Import Errors

If you get import errors for `mlsys`:

```bash
# Ensure dependencies are installed
uv sync

# Verify package is installed
uv pip list | grep mlsys
```

### BigQuery Authentication

Ensure you have GCP credentials configured:

```bash
# Set via environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Or authenticate with gcloud
gcloud auth application-default login
```

### GCS Upload Failures

Check that:
1. Bucket exists and you have write permissions
2. Bucket name is correct in `.env`
3. Object is serializable (use `joblib.dump()` for sklearn models)

## Resources

- [scikit-learn Documentation](https://scikit-learn.org/)
- [pandas Documentation](https://pandas.pydata.org/)
- [BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery/latest)
- [GCS Python Client](https://cloud.google.com/python/docs/reference/storage/latest)
