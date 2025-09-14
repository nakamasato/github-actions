# Enhanced Cloud Run Deploy Action

A GitHub Action that extends `google-github-actions/deploy-cloudrun@v3` with advanced PR deployment and traffic management features.

## Features

- **PR Deployments**: Automatically deploy PRs with zero traffic allocation using tagged revisions (`pr-<number>`)
- **Main Branch Deployments**: Deploy to production with 100% traffic allocation
- **Smart PR Comments**: Automatically create/update PR comments with deployment details and cleanup status
- **Flexible Configuration**: Support for environment variables, secrets, and resource limits
- **Deployment Summary**: Rich GitHub Step Summary with deployment details

## Example

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]
    paths:
      - 'src/**'
      - '.github/workflows/deploy-cloudrun.yml'
  pull_request:
    types: [opened, synchronize, labeled, closed]
    paths:
      - 'src/**'
      - '.github/workflows/deploy-cloudrun.yml'
  release:
    types: [published]

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
    # Deploy on release, main push, or PR with 'deploy' label
    if: |
      github.event_name == 'release' ||
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
          if [ "${{ github.event_name }}" = "release" ]; then
            echo "ENVIRONMENT=prod" >> "$GITHUB_OUTPUT"
          elif [ "${{ github.event_name }}" = "push" ] && [ "${{ github.ref }}" = "refs/heads/main" ]; then
            echo "ENVIRONMENT=dev" >> "$GITHUB_OUTPUT"
          else
            echo "ENVIRONMENT=pr" >> "$GITHUB_OUTPUT"
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
          context: .
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/${{ env.SERVICE_NAME }}:${{ steps.env.outputs.IMAGE_TAG }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Deploy to Cloud Run
        id: deploy
        uses: nakamasato/github-actions/deploy-cloudrun@main
        with:
          service: ${{ env.SERVICE_NAME }}
          image: ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/${{ env.SERVICE_NAME }}:${{ steps.env.outputs.IMAGE_TAG }}
          region: ${{ env.REGION }}
          project_id: ${{ env.PROJECT_ID }}
          environment: ${{ steps.env.outputs.ENVIRONMENT }}
          github_token: ${{ secrets.GITHUB_TOKEN }}

  cleanup-pr-traffic-tag:
    # Clean up PR deployments when PR is closed
    if: github.event_name == 'pull_request' && github.event.action == 'closed'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
      pull-requests: write  # Required for PR comments

    steps:
      - name: Cleanup PR deployment
        uses: nakamasato/github-actions/cleanup-cloudrun-traffic-tag@main
        with:
          service: ${{ env.SERVICE_NAME }}
          tag: 'pr-${{ github.event.pull_request.number }}'
          region: ${{ env.REGION }}
          project_id: ${{ env.PROJECT_ID }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

This action extends [google-github-actions/deploy-cloudrun@v3](https://github.com/google-github-actions/deploy-cloudrun) and supports all of its inputs.

### Upstream Inputs

All inputs from the base action are supported. See the [official documentation](https://github.com/google-github-actions/deploy-cloudrun#inputs) for the complete list, including:
- `service`, `image`, `source`, `suffix`
- `env_vars`, `secrets`, `labels`
- `timeout`, `flags`, `tag`
- `no_traffic`, `revision_traffic`, `tag_traffic`
- `project_id`, `region`
- And more...

### Additional Inputs (Specific to This Action)

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `environment` | Deployment environment (dev, staging, prod) - also creates and updates GitHub deployment status when specified | | `dev` |
| `github_token` | GitHub token for PR comments | | `${{ github.token }}` |
| `no_traffic` | Deploy with no traffic allocation | | `${{ github.event_name == 'pull_request' }}` |
| `revision_traffic` | Traffic allocation for the deployed revision | | `${{ github.event_name != 'pull_request' && 'LATEST=100' || '' }}` |

### Automatic Behavior

This action automatically configures deployments based on context:
- **PR Deployments**: Tagged as `pr-{number}` with no traffic allocation
- **Main Branch Deployments**: Receives 100% traffic allocation to latest revision
- **GitHub Deployments**: When `environment` is specified, creates and updates GitHub deployment status for tracking

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

For PR cleanup with commenting support, see the [cleanup-cloudrun-traffic-tag action](../cleanup-cloudrun-traffic-tag/).

## Prerequisites

1. **Authentication**: This action requires Google Cloud authentication to be set up before use. Use [google-github-actions/auth](https://github.com/google-github-actions/auth) before calling this action:
   ```yaml
   - uses: google-github-actions/auth@v3
     with:
       workload_identity_provider: ${{ env.WORKLOAD_IDENTITY_POOL_PROVIDER }}
       service_account: ${{ env.SERVICE_ACCOUNT }}
   ```

2. **Google Cloud Setup**:
   - Enable Cloud Run API
   - Set up Workload Identity Federation
   - Create a service account with Cloud Run Admin permissions

3. **GitHub Repository**:
   - Configure repository secrets for sensitive data
   - Set up proper permissions for the workflow

4. **Container Registry**:
   - Set up Artifact Registry or Container Registry
   - Ensure proper authentication

## Troubleshooting

### Common Issues

1. **Authentication Issues**:
   - Verify Workload Identity Federation setup
   - Check service account permissions
   - Ensure `id-token: write` permission is set

2. **PR URLs Not Working**:
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
