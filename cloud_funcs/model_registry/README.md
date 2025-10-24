# Model Registry Cloud Function

This Cloud Function automatically registers model metadata in BigQuery when new model artifacts are uploaded to GCS buckets (`ml-models-dev`, `ml-models-staging`, `ml-models-prod`).

## Overview

**Trigger**: Cloud Storage object finalize event (new file uploaded)
**Action**: Extract metadata and insert into BigQuery `ml_registry.models` table
**Tracked Metadata**:
- Model name
- Model version
- Environment (dev/staging/prod)
- GCS bucket and path
- File size
- Upload timestamp
- Uploader
- Registration timestamp

## Prerequisites

1. **GCP Project**: Ensure you're working in the correct GCP project (`soufianesys`)
2. **BigQuery Dataset**: Create `ml_registry` dataset if it doesn't exist
3. **BigQuery Table**: Create `models` table with the schema below
4. **IAM Permissions**: Cloud Function service account needs BigQuery Data Editor role

## BigQuery Table Schema

Create the `ml_registry.models` table with this schema:

```bash
bq mk --dataset --location=us-central1 soufianesys:ml_registry

bq mk --table \
  soufianesys:ml_registry.models \
  model_name:STRING,model_version:INTEGER,environment:STRING,gcs_bucket:STRING,gcs_path:STRING,file_size_bytes:INTEGER,upload_timestamp:TIMESTAMP,uploader:STRING,registered_at:TIMESTAMP
```

Or using SQL:

```sql
CREATE TABLE `soufianesys.ml_registry.models` (
  model_name STRING NOT NULL,
  model_version INT64 NOT NULL,
  environment STRING NOT NULL,
  gcs_bucket STRING NOT NULL,
  gcs_path STRING NOT NULL,
  file_size_bytes INT64,
  upload_timestamp TIMESTAMP,
  uploader STRING,
  registered_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(registered_at)
CLUSTER BY model_name, environment, model_version;
```

## Deployment

### Deploy for Dev Environment

```bash
gcloud functions deploy model-registry-dev \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=register_model \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=ml-models-dev" \
  --set-env-vars GCP_PROJECT_ID=soufianesys \
  --service-account=model-registry-sa-dev@soufianesys.iam.gserviceaccount.com \
  --max-instances=5 \
  --memory=256MB \
  --timeout=60s
```

### Deploy for Staging Environment

```bash
gcloud functions deploy model-registry-staging \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=register_model \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=ml-models-staging" \
  --set-env-vars GCP_PROJECT_ID=soufianesys \
  --service-account=model-registry-sa-staging@soufianesys.iam.gserviceaccount.com \
  --max-instances=5 \
  --memory=256MB \
  --timeout=60s
```

### Deploy for Prod Environment

```bash
gcloud functions deploy model-registry-prod \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=register_model \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=ml-models-prod" \
  --set-env-vars GCP_PROJECT_ID=soufianesys \
  --service-account=model-registry-sa-prod@soufianesys.iam.gserviceaccount.com \
  --max-instances=5 \
  --memory=256MB \
  --timeout=60s
```

## Service Account Setup

Create service accounts for each environment with required permissions:

```bash
# Create service account for dev
gcloud iam service-accounts create model-registry-sa-dev \
  --display-name="Model Registry Cloud Function - Dev"

# Grant BigQuery Data Editor role
gcloud projects add-iam-policy-binding soufianesys \
  --member="serviceAccount:model-registry-sa-dev@soufianesys.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# Grant BigQuery Job User role (needed to run queries/inserts)
gcloud projects add-iam-policy-binding soufianesys \
  --member="serviceAccount:model-registry-sa-dev@soufianesys.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

# Repeat for staging and prod environments
```

## Testing

### Upload a Test Model

```bash
# Upload a test file to dev bucket
echo "test model" > test_model.pkl
gsutil cp test_model.pkl gs://ml-models-dev/titanic-survival/v1/model.pkl
```

### Verify Registration

Query BigQuery to verify the model was registered:

```bash
bq query --use_legacy_sql=false \
  "SELECT * FROM \`soufianesys.ml_registry.models\`
   WHERE model_name = 'titanic-survival'
   ORDER BY registered_at DESC
   LIMIT 5"
```

### View Function Logs

```bash
gcloud functions logs read model-registry-dev \
  --region=us-central1 \
  --limit=50
```

## Expected GCS Path Format

The function expects model artifacts to be uploaded with this path structure:

```
gs://{bucket}/{model_name}/v{version}/{file_name}
```

**Examples**:
- `gs://ml-models-dev/titanic-survival/v1/model.pkl`
- `gs://ml-models-staging/fraud-detection/v3/pipeline.pkl`
- `gs://ml-models-prod/churn-prediction/v2/model.joblib`

**Invalid paths** (will be skipped):
- `gs://ml-models-dev/model.pkl` (missing model name and version)
- `gs://ml-models-dev/titanic-survival/model.pkl` (missing version)
- `gs://ml-models-dev/titanic-survival/1.0/model.pkl` (version must be v{N})

## Monitoring

Monitor function execution and errors:

```bash
# View function details
gcloud functions describe model-registry-dev --region=us-central1 --gen2

# View metrics in Cloud Console
# Navigate to: Cloud Functions > model-registry-dev > Metrics

# Set up alerts for failures
# Navigate to: Cloud Monitoring > Alerting
# Create alert: Cloud Function execution errors > threshold > notify
```

## Troubleshooting

### Function fails with "BigQuery table not found"

Ensure the `ml_registry.models` table exists:

```bash
bq show soufianesys:ml_registry.models
```

If it doesn't exist, create it using the schema above.

### Function fails with "Permission denied"

Verify the service account has the required IAM roles:

```bash
gcloud projects get-iam-policy soufianesys \
  --flatten="bindings[].members" \
  --filter="bindings.members:model-registry-sa-dev@soufianesys.iam.gserviceaccount.com"
```

Should show `roles/bigquery.dataEditor` and `roles/bigquery.jobUser`.

### Model not registered despite successful upload

Check function logs for errors:

```bash
gcloud functions logs read model-registry-dev \
  --region=us-central1 \
  --limit=100
```

Verify the GCS path format matches the expected structure.

## Update Function

To update the function after making code changes:

```bash
# Navigate to this directory
cd scripts/model_registry

# Re-deploy (use same command as initial deployment)
gcloud functions deploy model-registry-dev \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=register_model \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=ml-models-dev" \
  --set-env-vars GCP_PROJECT_ID=soufianesys \
  --service-account=model-registry-sa-dev@soufianesys.iam.gserviceaccount.com \
  --max-instances=5 \
  --memory=256MB \
  --timeout=60s
```

## Delete Function

To delete the function:

```bash
gcloud functions delete model-registry-dev --region=us-central1 --gen2
```

## Notes

- The function is event-driven and runs automatically on GCS uploads
- Each environment (dev/staging/prod) has its own function instance
- Model registry provides full model lineage and history across environments
- Use the BigQuery table for model inventory, versioning, and auditing
- Function is idempotent: re-uploading the same file will create a new registry entry
