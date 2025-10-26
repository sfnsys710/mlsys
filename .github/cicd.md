# CI/CD Workflows

GitHub Actions workflows for automated deployment across dev, staging, and prod environments.

## Architecture

**Three-tier modular workflow design**:

1. **Reusable Workflows** - Parameterized building blocks
   - `terraform.yml` - Infrastructure deployment (Terraform)
   - `docker.yml` - Docker image build/push (Artifact Registry)
   - `airflow.yml` - DAG deployment (Composer)

2. **Main Workflows** - Environment-specific deployment triggers
   - `pr.yml` - Dev auto-deployment with smart change detection
   - `staging.yml` - Staging manual deployment (all components)
   - `prod.yml` - Production manual deployment with confirmation (all components)

## Progressive Deployment Strategy

```
dev (automatic, selective) → staging (manual, all) → prod (manual, all + confirmation)
```

### Dev Environment (Automatic with Smart Detection)
- **Trigger**: Pull request to `main`
- **Deployment**: Selective based on changed files
  - Terraform: Only if `infra/` changes
  - Docker: Only if code changes (src/, scripts/, Dockerfile, etc.)
  - Airflow: Only if `dags/` changes
- **Tag**: `{git-sha}` (e.g., `a1b2c3d`)
- **Purpose**: Continuous testing and validation
- **Workflow**: `pr.yml`

### Staging Environment (Manual, All Components)
- **Trigger**: Manual via GitHub Actions UI
- **Deployment**: Always deploys all three components
  - Terraform (infrastructure)
  - Docker (application image)
  - Airflow (DAGs)
- **Tag**: `v{version}` from `pyproject.toml` (e.g., `v0.1.5`)
- **Purpose**: Pre-production validation
- **Workflow**: `staging.yml`

### Production Environment (Manual with Confirmation, All Components)
- **Trigger**: Manual via GitHub Actions UI
- **Deployment**: Always deploys all three components
  - Terraform (infrastructure)
  - Docker (application image)
  - Airflow (DAGs)
- **Tag**: `v{version}` from `pyproject.toml` (e.g., `v0.1.5`)
- **Purpose**: Production deployment
- **Safety**: Must type "production" to confirm
- **Workflow**: `prod.yml`

## Workflow Details

### 1. pr.yml - PR/Dev Deployment (Smart Detection)

**Triggered by**: Pull request to `main` branch

**Pipeline**:
```
Pre-commit checks
    ↓
Change detection (infra, code, dags)
    ↓
Terraform (dev) ← Only if infra/ changed
    ↓
Docker (dev) ← Only if code changed
    ↓
Airflow (dev) ← Only if dags/ changed
```

**Features**:
- Runs all pre-commit hooks (ruff, detect-secrets, etc.)
- Smart change detection for efficiency
- Selective deployment based on changed files
- Each component runs independently if its files changed
- Concurrency: Cancels old runs for same PR

**Change Detection Rules**:
```yaml
Infrastructure (infra/):
- infra/**

Code (triggers Docker build):
- src/**
- mlsys/**
- scripts/**
- pyproject.toml
- uv.lock
- Dockerfile
- .dockerignore

DAGs (triggers Airflow deployment):
- dags/**
```

**Example Scenarios**:
- **Only change infra/**: Deploys Terraform only
- **Only change src/**: Deploys Docker only
- **Only change dags/**: Deploys DAGs only
- **Change src/ + dags/**: Deploys Docker + Airflow
- **Change all three**: Deploys Terraform + Docker + Airflow

### 2. staging.yml - Staging Deployment (All Components)

**Triggered by**: Manual workflow dispatch

**Pipeline**:
```
Terraform (staging)
    ↓
Extract version from pyproject.toml
    ↓
Docker (staging) with version tag
    ↓
Airflow (staging) - Deploy all DAGs
```

**Usage**:
1. Go to Actions → Staging Deployment
2. Click "Run workflow"
3. Confirm execution

**Deployment**:
- **Always deploys all three components** (no change detection)
- Infrastructure, application, and DAGs deployed together
- Version tag from `pyproject.toml` (e.g., `v0.1.5`)

### 3. prod.yml - Production Deployment (All Components with Confirmation)

**Triggered by**: Manual workflow dispatch with confirmation

**Pipeline**:
```
Validate confirmation input ("production")
    ↓
Terraform (prod)
    ↓
Extract version from pyproject.toml
    ↓
Docker (prod) with version tag
    ↓
Airflow (prod) - Deploy all DAGs
```

**Usage**:
1. Go to Actions → Production Deployment
2. Click "Run workflow"
3. **Type "production"** in the confirmation field
4. Confirm execution

**Deployment**:
- **Always deploys all three components** (no change detection)
- Infrastructure, application, and DAGs deployed together
- Version tag from `pyproject.toml` (e.g., `v0.1.5`)

**Safety Features**:
- Confirmation gate (must type "production")
- Concurrency protection (prevents simultaneous deployments)
- No auto-cancel (runs to completion)

## Reusable Workflows

### terraform.yml

**Purpose**: Deploy infrastructure with Terraform

**Inputs**:
- `environment` - dev/staging/prod
- `terraform_action` - plan or apply
- `gcp_region` - GCP region
- `gcp_project_id` - GCP project ID

**Secrets**:
- `gcp_sa_key` - GCP service account JSON key

**What it does**:
1. Reads Terraform version from `infra/.terraform-version`
2. Authenticates to GCP
3. Initializes Terraform with environment-specific state bucket
4. Runs format check, validate, plan
5. Applies changes if `terraform_action=apply`

**Working Directory**: `infra/envs/{environment}/`

**State Buckets**:
- Dev: `mlsys-terraform-state-dev`
- Staging: `mlsys-terraform-state-staging`
- Prod: `mlsys-terraform-state-prod`

### docker.yml

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

**Image Tags**:
- Dev: commit SHA (e.g., `a1b2c3d`)
- Staging/Prod: version from pyproject.toml (e.g., `v0.1.5`)

### airflow.yml

**Purpose**: Deploy DAGs to Airflow Composer

**Inputs**:
- `environment` - dev/staging/prod

**Secrets**:
- `gcp_sa_key` - GCP service account JSON key

**What it does**:
1. Authenticates to GCP
2. Checks for DAG files in `dags/` directory
3. Uploads all `.py` files to `gs://mlsys-composer-{env}/dags/`

**Notes**:
- Deploys all DAG files found in `dags/` directory
- Skips if no DAG files exist (graceful handling)

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

### 1. Feature Development (Dev Environment)

```bash
# Create feature branch
git checkout -b feature-my-new-feature

# Make changes to infrastructure, code, or DAGs
# ... edit files ...

# Push and create PR
git push origin feature-my-new-feature
gh pr create --title "Add new feature"
```

**What happens automatically**:
- Pre-commit checks run
- Change detection determines what to deploy:
  - Changed `infra/`? → Deploy Terraform
  - Changed `src/`? → Build and push Docker image
  - Changed `dags/`? → Deploy DAGs to Composer
- Only changed components are deployed (efficiency)
- Changes are live in dev environment

### 2. Staging Validation (All Components)

Once PR is merged to main:

1. Go to Actions → Staging Deployment
2. Click "Run workflow"
3. Wait for deployment to complete

**What happens**:
- Deploys **all three components** (infrastructure, Docker, DAGs)
- Uses version from `pyproject.toml`
- Test in staging environment
- Validate everything works as expected

### 3. Production Release (All Components with Confirmation)

After staging validation:

1. Ensure `pyproject.toml` version is updated (e.g., `0.1.6`)
2. Go to Actions → Production Deployment
3. Click "Run workflow"
4. Type "production" in confirmation field
5. Click "Run workflow"

**What happens**:
- Validates confirmation input
- Deploys **all three components** (infrastructure, Docker, DAGs)
- Uses version from `pyproject.toml`
- Monitor deployment
- Verify production environment

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
- Verify DAG files exist in `dags/` directory
- Check Composer bucket exists
- Ensure service account has storage write permissions

**Change detection not working**:
- Verify paths in `dorny/paths-filter` configuration
- Check GitHub Actions logs for filter output
- Ensure files are actually changed in the PR

## Best Practices

1. **Let smart detection work for you** - PR workflow automatically deploys only what changed
2. **Test in dev via PR** - All changes automatically deploy to dev
3. **Manual staging deployment** - Use when ready for pre-production testing
4. **Update version before prod** - Bump `pyproject.toml` version
5. **Use confirmation gate** - Always type "production" carefully
6. **Monitor deployments** - Watch workflow logs during deployment
7. **Small, incremental changes** - Easier to debug and rollback
8. **Trust the automation** - Change detection prevents unnecessary deployments

## Understanding Change Detection

### Dev (PR) Environment - Selective Deployment

**Goal**: Deploy only what changed for efficiency

**Pattern**:
- Change `infra/modules/mlsys/variables.tf` → Deploys Terraform only
- Change `src/mlsys/bq.py` → Deploys Docker only
- Change `dags/my_model_dag.py` → Deploys DAGs only
- Change multiple areas → Deploys all affected components

**Benefits**:
- Faster CI/CD runs
- Reduced resource usage
- Clear feedback on what's being deployed

### Staging/Prod Environments - Full Deployment

**Goal**: Ensure complete, consistent deployments

**Pattern**:
- **Always** deploys all three components
- No change detection
- Complete environment refresh

**Benefits**:
- Guaranteed consistency across components
- No risk of partial deployments
- Simpler mental model for releases

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
- Change detection logs show exactly what's being deployed
