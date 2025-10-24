# CI/CD Workflows

GitHub Actions workflows for automated deployment across dev, staging, and prod environments.

## Architecture

**Three-tier modular workflow design**:

1. **Reusable Workflows** - Parameterized building blocks
   - `docker-build.yml` - Docker image build/push
   - `terraform-workflow.yml` - Infrastructure deployment

2. **Main Workflows** - Environment-specific deployment triggers
   - `pr.yml` - Dev auto-deployment
   - `staging.yml` - Staging manual deployment
   - `prod.yml` - Production manual deployment (with confirmation)

3. **Utility Workflows**
   - `deploy-dag.yml` - DAG deployment to Composer

## Progressive Deployment Strategy

```
dev (automatic) → staging (manual) → prod (manual + confirmation)
```

### Dev Environment (Automatic)
- **Trigger**: Pull request to `main`
- **Tag**: `{git-sha}` (e.g., `a1b2c3d`)
- **Purpose**: Continuous testing and validation
- **Workflow**: `pr.yml`

### Staging Environment (Manual)
- **Trigger**: Manual via GitHub Actions UI
- **Tag**: `v{version}` from `pyproject.toml` (e.g., `v0.1.5`)
- **Purpose**: Pre-production validation
- **Workflow**: `staging.yml`

### Production Environment (Manual with Confirmation)
- **Trigger**: Manual via GitHub Actions UI
- **Tag**: `v{version}` from `pyproject.toml` (e.g., `v0.1.5`)
- **Purpose**: Production deployment
- **Safety**: Must type "production" to confirm
- **Workflow**: `prod.yml`

## Workflow Details

### 1. pr.yml - PR/Dev Deployment

**Triggered by**: Pull request to `main` branch

**Pipeline**:
```
Pre-commit checks
    ↓
Code change detection
    ↓
Terraform (dev)
    ↓
Docker build (dev) ← Only if code changed
```

**Features**:
- Runs all pre-commit hooks (ruff, detect-secrets, etc.)
- Smart code change detection (skips Docker if only docs/infra changed)
- Auto-applies infrastructure changes to dev
- Builds and pushes Docker image with commit SHA tag
- Concurrency: Cancels old runs for same PR

**Code Change Detection**:
```yaml
Triggers Docker build only if these paths change:
- src/**
- mlsys/**
- scripts/**
- pyproject.toml
- uv.lock
- Dockerfile
- .dockerignore
```

### 2. staging.yml - Staging Deployment

**Triggered by**: Manual workflow dispatch

**Pipeline**:
```
Terraform (staging)
    ↓
Extract version from pyproject.toml
    ↓
Docker build (staging) with version tag
```

**Usage**:
1. Go to Actions → Staging Deployment
2. Click "Run workflow"
3. Confirm execution

**Image Tag**: Uses semantic version from `pyproject.toml` (e.g., `v0.1.5`)

### 3. prod.yml - Production Deployment

**Triggered by**: Manual workflow dispatch with confirmation

**Pipeline**:
```
Validate confirmation input
    ↓
Terraform (prod)
    ↓
Extract version from pyproject.toml
    ↓
Docker build (prod) with version tag
```

**Usage**:
1. Go to Actions → Production Deployment
2. Click "Run workflow"
3. **Type "production"** in the confirmation field
4. Confirm execution

**Safety Features**:
- Confirmation gate (must type "production")
- Concurrency protection (prevents simultaneous deployments)
- No auto-cancel (runs to completion)

**Image Tag**: Uses semantic version from `pyproject.toml` (e.g., `v0.1.5`)

### 4. deploy-dag.yml - DAG Deployment

**Triggered by**: Manual workflow dispatch

**Purpose**: Deploy Airflow DAGs to Composer buckets

**Usage**:
1. Go to Actions → Deploy DAG to Composer
2. Click "Run workflow"
3. Select environment (dev/staging/prod)
4. Enter DAG filename (e.g., `titanic_survival_dag.py`)
5. Confirm execution

**What it does**:
- Validates DAG file exists in `dags/` directory
- Uploads DAG to `gs://mlsys-composer-{env}/dags/`
- Provides deployment confirmation

**Example**:
```bash
Environment: dev
DAG filename: titanic_survival_dag.py
→ Uploads to: gs://mlsys-composer-dev/dags/titanic_survival_dag.py
```

## Reusable Workflows

### docker-build.yml

**Purpose**: Build and push Docker images to Artifact Registry

**Inputs**:
- `environment` - dev/staging/prod
- `image_tag` - Tag for the image (e.g., git SHA or version)
- `gcp_region` - GCP region
- `gcp_project_id` - GCP project ID

**Secrets**:
- `gcp_sa_key` - GCP service account JSON key

**What it does**:
1. Authenticates to GCP
2. Configures Docker for Artifact Registry
3. Builds image with specified tag + latest
4. Pushes to `{region}-docker.pkg.dev/{project}/mlsys-{env}/mlsys:{tag}`

### terraform-workflow.yml

**Purpose**: Deploy infrastructure with Terraform

**Inputs**:
- `environment` - dev/staging/prod
- `terraform_action` - plan or apply
- `gcp_region` - GCP region
- `gcp_project_id` - GCP project ID

**Secrets**:
- `gcp_sa_key` - GCP service account JSON key

**What it does**:
1. Reads Terraform version from `.terraform-version`
2. Authenticates to GCP
3. Initializes Terraform with environment-specific state bucket
4. Runs format check, validate, plan
5. Applies changes if `terraform_action=apply`

**Working Directory**: `infra/envs/{environment}/`

**State Buckets**:
- Dev: `mlsys-terraform-state-dev`
- Staging: `mlsys-terraform-state-staging`
- Prod: `mlsys-terraform-state-prod`

## Prerequisites

### GitHub Secrets and Variables

**Environment**: `gcp` (single environment, used by all workflows)

**Secret**:
- `SA` - GCP service account JSON key with permissions:
  - Artifact Registry Writer
  - Storage Admin
  - BigQuery Admin
  - IAM Service Account Admin
  - Project IAM Admin

**Variables**:
- `GCP_PROJECT_ID` - Your GCP project ID (e.g., `soufianesys`)
- `GCP_REGION` - GCP region (e.g., `us-central1`)

### Setup Instructions

1. **Create GCP Service Account**:
   ```bash
   gcloud iam service-accounts create github-actions \
     --display-name="GitHub Actions CI/CD"

   gcloud projects add-iam-policy-binding soufianesys \
     --member="serviceAccount:github-actions@soufianesys.iam.gserviceaccount.com" \
     --role="roles/editor"

   gcloud iam service-accounts keys create github-sa-key.json \
     --iam-account=github-actions@soufianesys.iam.gserviceaccount.com
   ```

2. **Configure GitHub Secrets**:
   - Go to repo Settings → Secrets and variables → Actions
   - Create environment: `gcp`
   - Add secret `SA` with contents of `github-sa-key.json`
   - Add variables:
     - `GCP_PROJECT_ID` = `soufianesys`
     - `GCP_REGION` = `us-central1`

3. **Create Terraform State Buckets**:
   ```bash
   # See infra/README.md for detailed instructions
   gcloud storage buckets create gs://mlsys-terraform-state-dev ...
   gcloud storage buckets create gs://mlsys-terraform-state-staging ...
   gcloud storage buckets create gs://mlsys-terraform-state-prod ...
   ```

## Typical Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature-my-new-model

# Make changes
# ... edit code ...

# Push and create PR
git push origin feature-my-new-model
gh pr create --title "Add new model"
```

**What happens**:
- `pr.yml` workflow triggers automatically
- Pre-commit checks run
- Infrastructure deploys to dev
- Docker image builds (if code changed)
- Changes are live in dev environment

### 2. Staging Validation

Once PR is merged to main:

1. Go to Actions → Staging Deployment
2. Click "Run workflow"
3. Wait for deployment to complete
4. Test in staging environment
5. Validate everything works as expected

### 3. Production Release

After staging validation:

1. Ensure `pyproject.toml` version is updated
2. Go to Actions → Production Deployment
3. Click "Run workflow"
4. Type "production" in confirmation field
5. Click "Run workflow"
6. Monitor deployment
7. Verify production environment

### 4. Deploy DAG

When you have a new or updated DAG:

1. Place DAG file in `dags/` directory
2. Commit and merge to main
3. Go to Actions → Deploy DAG to Composer
4. Select environment (start with dev)
5. Enter DAG filename (e.g., `my_model_dag.py`)
6. Click "Run workflow"
7. Repeat for staging and prod as needed

## Concurrency Control

**PR Workflow**:
- Group: `pr-{pr_number}`
- Cancel in progress: `true` (new commits cancel old runs)

**Staging Workflow**:
- Group: `staging-deployment`
- Cancel in progress: `false` (waits for completion)

**Production Workflow**:
- Group: `production-deployment`
- Cancel in progress: `false` (prevents accidental cancellation)

## Monitoring and Debugging

### View Workflow Runs

1. Go to repository → Actions tab
2. Select workflow from left sidebar
3. Click on specific run to see details
4. Expand job steps to see logs

### Common Issues

**Terraform state lock**:
- Wait for other runs to complete
- Or manually unlock: `terraform force-unlock <lock-id>`

**Docker build fails**:
- Check if Artifact Registry exists
- Verify service account has write permissions
- Check Dockerfile syntax

**DAG deployment fails**:
- Verify DAG file exists in `dags/` directory
- Check Composer bucket exists
- Ensure service account has storage write permissions

## Best Practices

1. **Always test in dev first** - PR workflow automatically deploys to dev
2. **Validate in staging** - Manual staging deployment before prod
3. **Update version numbers** - Bump `pyproject.toml` version before prod deployment
4. **Use confirmation gate** - Always type "production" carefully
5. **Monitor deployments** - Watch workflow logs during deployment
6. **Small, incremental changes** - Easier to debug and rollback
7. **Code change detection** - Leverage automatic skipping for efficiency

## Rollback Strategy

If production deployment fails or has issues:

1. **Revert code changes**:
   ```bash
   git revert <commit-sha>
   git push origin main
   ```

2. **Redeploy previous version**:
   - Update `pyproject.toml` to previous version
   - Run prod workflow with "production" confirmation

3. **Terraform rollback**:
   ```bash
   cd infra/envs/prod
   terraform init -backend-config="bucket=mlsys-terraform-state-prod"
   terraform plan -var="project_id=..." -var="region=..."
   # Review plan and apply if safe
   ```

## Security Notes

- Service account key stored as GitHub secret
- Secrets never logged or exposed in workflow output
- Production requires manual confirmation
- All deployments are audited in GitHub Actions logs
- State buckets have versioning enabled for recovery
