# cleanup-cloudrun

GitHub Action to clean up Cloud Run services deployed by the `deploy-cloudrun` action.

## Description

This action removes Cloud Run services that were deployed for pull request previews or temporary environments. It's typically used when a pull request is closed or merged.

## Usage

```yaml
name: Cleanup Cloud Run on PR Close

on:
  pull_request:
    types: [closed]

jobs:
  cleanup:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
      pull-requests: write
    steps:
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v3
        with:
          workload_identity_provider: ${{ env.WORKLOAD_IDENTITY_POOL_PROVIDER }}
          service_account: ${{ env.SERVICE_ACCOUNT }}

      - uses: nakamasato/github-actions/cleanup-cloudrun@main
        with:
          service: 'my-app'
          environment: 'pr'
          region: 'us-central1'
          project_id: 'my-project-id'
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

| Name | Description | Required | Default |
|------|-------------|----------|---------|
| `service` | Cloud Run service name | Yes | - |
| `region` | Google Cloud region | Yes | - |
| `project_id` | Google Cloud project ID | Yes | - |
| `environment` | Deployment environment | No | `dev` |
| `github_token` | GitHub token for PR comments | No | `${{ github.token }}` |
| `pr_number` | PR number (auto-detected if not provided) | No | - |

## Outputs

This action does not produce any outputs.

## Requirements

- Google Cloud Platform project with Cloud Run API enabled
- Service account with `roles/run.admin` permission
- Workload Identity Federation configured for GitHub Actions authentication

## Example Workflow

See the deploy-cloudrun README for a complete example that includes both deployment and cleanup actions.
