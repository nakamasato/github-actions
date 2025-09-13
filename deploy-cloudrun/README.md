# Enhanced Cloud Run Deploy Action

A GitHub Action that extends `google-github-actions/deploy-cloudrun@v2` with advanced PR deployment and traffic management features.

## Features

- **PR Deployments**: Automatically deploy PRs with zero traffic allocation using tagged revisions (`pr-<number>`)
- **Main Branch Deployments**: Deploy to production with 100% traffic allocation
- **Smart PR Comments**: Automatically create/update PR comments with deployment details and cleanup status
- **Health Checks**: Built-in health check validation with configurable timeout
- **Revision Cleanup**: Automatically clean up old revisions to prevent accumulation
- **Flexible Configuration**: Support for environment variables, secrets, and resource limits
- **Deployment Summary**: Rich GitHub Step Summary with deployment details

## Usage

### Basic Usage

```yaml
- name: Deploy to Cloud Run
  uses: ./deploy-cloudrun
  with:
    service: 'my-service'
    image: 'gcr.io/my-project/my-app:${{ github.sha }}'
    region: 'us-central1'
    project_id: 'my-project'
    workload_identity_provider: 'projects/123/locations/global/workloadIdentityPools/pool/providers/provider'
    service_account: 'github-actions@my-project.iam.gserviceaccount.com'
```

### Complete Workflow Example

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]
    paths:
      - 'frontend/**'
      - '.github/workflows/deploy-cloudrun.yml'
  pull_request:
    types: [opened, synchronize, labeled, closed]
    paths:
      - 'frontend/**'
      - '.github/workflows/deploy-cloudrun.yml'
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'dev'
        type: choice
        options:
        - dev
        - staging
        - prod

env:
  PROJECT_ID: your-project-id
  REGION: us-central1
  SERVICE_NAME: my-app
  REGISTRY: us-central1-docker.pkg.dev
  REPOSITORY: my-repo
  WORKLOAD_IDENTITY_POOL_PROVIDER: projects/123456789/locations/global/workloadIdentityPools/github/providers/github-provider
  SERVICE_ACCOUNT: github-actions@your-project-id.iam.gserviceaccount.com

jobs:
  build-and-deploy:
    # Deploy on main push, manual trigger, or PR with 'deploy' label
    if: |
      github.event_name == 'workflow_dispatch' ||
      github.event_name == 'push' ||
      (github.event_name == 'pull_request' &&
       github.event.action != 'closed' &&
       contains(github.event.pull_request.labels.*.name, 'deploy'))

    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
      deployments: write
      pull-requests: write  # Required for PR comments

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Determine environment
        id: env
        run: |
          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            echo "ENVIRONMENT=${{ github.event.inputs.environment }}" >> "$GITHUB_OUTPUT"
          elif [ "${{ github.ref }}" = "refs/heads/main" ]; then
            echo "ENVIRONMENT=prod" >> "$GITHUB_OUTPUT"
          else
            echo "ENVIRONMENT=dev" >> "$GITHUB_OUTPUT"
          fi
          echo "IMAGE_TAG=$(echo "$GITHUB_SHA" | cut -c1-7)" >> "$GITHUB_OUTPUT"

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v3
        id: auth
        with:
          token_format: access_token
          workload_identity_provider: ${{ env.WORKLOAD_IDENTITY_POOL_PROVIDER }}
          service_account: ${{ env.SERVICE_ACCOUNT }}

      - name: Login to Artifact Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: oauth2accesstoken
          password: ${{ steps.auth.outputs.access_token }}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: frontend
          file: frontend/Dockerfile
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/${{ env.SERVICE_NAME }}:${{ steps.env.outputs.IMAGE_TAG }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            NODE_ENV=production

      - name: Deploy to Cloud Run
        id: deploy
        uses: nakamasato/github-actions/deploy-cloudrun@main
        with:
          service: ${{ env.SERVICE_NAME }}
          image: ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/${{ env.SERVICE_NAME }}:${{ steps.env.outputs.IMAGE_TAG }}
          region: ${{ env.REGION }}
          project_id: ${{ env.PROJECT_ID }}
          environment: ${{ steps.env.outputs.ENVIRONMENT }}
          workload_identity_provider: ${{ env.WORKLOAD_IDENTITY_POOL_PROVIDER }}
          service_account: ${{ env.SERVICE_ACCOUNT }}
          # Resource configuration
          cpu: '2'
          memory: '1Gi'
          max_instances: '20'
          min_instances: '1'
          timeout: '300'
          # Environment variables
          env_vars: |
            NODE_ENV=production
            LOG_LEVEL=info
            PORT=8080
            ENVIRONMENT=${{ steps.env.outputs.ENVIRONMENT }}
          # Secrets (stored in Google Secret Manager)
          secrets: |
            DATABASE_URL=database-url-secret
            API_KEY=api-key-secret
          # Health check configuration
          health_check_path: '/api/health'
          health_check_timeout: '60'
          # Cleanup configuration
          cleanup_old_revisions: '5'
          # GitHub token for PR comments (automatically provided)
          github_token: ${{ secrets.GITHUB_TOKEN }}

      - name: Create GitHub deployment
        if: success()
        uses: actions/github-script@v7
        with:
          script: |
            const deployment = await github.rest.repos.createDeployment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              ref: context.sha,
              environment: '${{ steps.env.outputs.ENVIRONMENT }}',
              description: 'Deploy to Cloud Run ${{ steps.env.outputs.ENVIRONMENT }}',
              auto_merge: false,
              required_contexts: []
            });

            const deploymentUrl = '${{ github.event_name == "pull_request" && steps.deploy.outputs.pr_url || steps.deploy.outputs.url }}';

            await github.rest.repos.createDeploymentStatus({
              owner: context.repo.owner,
              repo: context.repo.repo,
              deployment_id: deployment.data.id,
              state: 'success',
              environment_url: deploymentUrl,
              description: 'Deployment successful'
            });

  cleanup-pr-deployment:
    # Clean up PR deployments when PR is closed
    if: github.event_name == 'pull_request' && github.event.action == 'closed'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
      pull-requests: write  # Required for PR comments

    steps:
      - name: Cleanup PR deployment
        uses: nakamasato/github-actions/cleanup-cloudrun@main
        with:
          service: ${{ env.SERVICE_NAME }}
          region: ${{ env.REGION }}
          project_id: ${{ env.PROJECT_ID }}
          environment: 'dev'
          workload_identity_provider: ${{ env.WORKLOAD_IDENTITY_POOL_PROVIDER }}
          service_account: ${{ env.SERVICE_ACCOUNT }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `service` | Cloud Run service name | ✅ | |
| `image` | Container image URL | ✅ | |
| `region` | Google Cloud region | ✅ | |
| `project_id` | Google Cloud project ID | ✅ | |
| `workload_identity_provider` | Workload Identity Provider | ✅ | |
| `service_account` | Service account email | ✅ | |
| `environment` | Deployment environment | | `dev` |
| `cpu` | CPU allocation | | `1` |
| `memory` | Memory allocation | | `512Mi` |
| `max_instances` | Maximum instances | | `10` |
| `min_instances` | Minimum instances | | `0` |
| `timeout` | Request timeout (seconds) | | `300` |
| `env_vars` | Environment variables (KEY=VALUE per line) | | |
| `secrets` | Secrets (KEY=SECRET_NAME per line) | | |
| `github_token` | GitHub token for PR comments | | `${{ github.token }}` |
| `health_check_path` | Health check endpoint | | `/api/health` |
| `health_check_timeout` | Health check timeout (seconds) | | `30` |
| `cleanup_old_revisions` | Number of revisions to keep | | `5` |

## Outputs

| Output | Description |
|--------|-------------|
| `url` | Service URL |
| `revision` | Deployed revision name |
| `pr_url` | PR-specific URL (for PR deployments only) |

## Deployment Behavior

### Pull Request Deployments

When deploying from a pull request:
- Service name: `{service}-{environment}` (e.g., `my-app-dev`)
- Traffic allocation: **0%** (no traffic)
- Tagged with: `pr-{number}` (e.g., `pr-123`)
- Accessible via: Tagged URL (`https://pr-123---my-app-dev-abc123-uc.a.run.app`)

### Main Branch Deployments

When deploying from main branch:
- Service name: `{service}-{environment}` (e.g., `my-app-prod`)
- Traffic allocation: **100%** (all traffic)
- No tag applied
- Accessible via: Service URL (`https://my-app-prod-abc123-uc.a.run.app`)

## Environment Variables and Secrets

### Environment Variables
Provide environment variables in `KEY=VALUE` format, one per line:

```yaml
env_vars: |
  NODE_ENV=production
  LOG_LEVEL=info
  PORT=8080
```

### Secrets
Provide secrets in `KEY=SECRET_NAME` format, one per line:

```yaml
secrets: |
  DATABASE_URL=database-url-secret
  API_KEY=api-key-secret
```

## Health Checks

The action performs automatic health checks after deployment:
- Default endpoint: `/api/health`
- Default timeout: 30 seconds
- Retries every 3 seconds
- Fails deployment if health check doesn't pass

Configure custom health check:

```yaml
health_check_path: '/health'
health_check_timeout: '60'
```

## Revision Management

The action automatically cleans up old revisions on main branch deployments:
- Keeps the latest N revisions (default: 5)
- Deletes older revisions to prevent accumulation
- Only runs on main branch deployments

Configure revision cleanup:

```yaml
cleanup_old_revisions: '10'  # Keep 10 latest revisions
```

## PR Comments

The action automatically manages PR comments for deployment status:

### Deployment Comments
- **Auto-create**: Creates a new comment when deploying a PR
- **Auto-update**: Updates existing comments instead of creating duplicates
- **Rich Details**: Includes preview URL, deployment details, and useful links
- **Smart Detection**: Uses HTML comments to identify and update existing comments

### Cleanup Comments
- **Cleanup Status**: Updates PR comments when deployments are cleaned up
- **Error Handling**: Shows cleanup status and troubleshooting info if cleanup fails
- **Graceful Degradation**: Action continues even if comment updates fail

### Required Permissions
For PR commenting to work, ensure your workflow has the correct permissions:

```yaml
permissions:
  contents: read
  id-token: write
  pull-requests: write  # Required for PR comments
```

### Disable PR Comments
To disable PR commenting, don't provide the `github_token` input or set it to an empty string:

```yaml
- uses: ./deploy-cloudrun
  with:
    # ... other inputs
    github_token: ''  # Disable PR comments
```

## Additional Actions

### Cleanup Action

For PR cleanup with commenting support, use the separate cleanup action:

```yaml
- name: Cleanup PR deployment
  uses: nakamasato/github-actions/cleanup-cloudrun@main
  with:
    service: 'my-service'
    region: 'us-central1'
    project_id: 'my-project'
    environment: 'dev'
    workload_identity_provider: 'projects/123/.../providers/provider'
    service_account: 'github-actions@my-project.iam.gserviceaccount.com'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

#### Cleanup Action Inputs
| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `service` | Cloud Run service name | ✅ | |
| `region` | Google Cloud region | ✅ | |
| `project_id` | Google Cloud project ID | ✅ | |
| `workload_identity_provider` | Workload Identity Provider | ✅ | |
| `service_account` | Service account email | ✅ | |
| `environment` | Deployment environment | | `dev` |
| `github_token` | GitHub token for PR comments | | `${{ github.token }}` |
| `pr_number` | PR number (auto-detected if not provided) | | |

## Prerequisites

1. **Google Cloud Setup**:
   - Enable Cloud Run API
   - Set up Workload Identity Federation
   - Create a service account with Cloud Run Admin permissions

2. **GitHub Repository**:
   - Configure repository secrets for sensitive data
   - Set up proper permissions for the workflow

3. **Container Registry**:
   - Set up Artifact Registry or Container Registry
   - Ensure proper authentication

## Troubleshooting

### Common Issues

1. **Health Check Failures**:
   - Verify your application responds to the health check endpoint
   - Check if the service is properly starting
   - Increase `health_check_timeout` if needed

2. **Authentication Issues**:
   - Verify Workload Identity Federation setup
   - Check service account permissions
   - Ensure `id-token: write` permission is set

3. **PR URLs Not Working**:
   - PR deployments receive 0% traffic by default
   - Use the tagged URL from the `pr_url` output
   - Verify the service is deployed successfully

### Debugging

Enable debug logging by setting:

```yaml
env:
  ACTIONS_STEP_DEBUG: 'true'
```

## License

This action is available under the MIT License.
