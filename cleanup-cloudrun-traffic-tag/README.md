# cleanup-cloudrun-traffic-tag

GitHub Action to clean up Cloud Run traffic tags for PR deployments deployed by the [deploy-cloudrun](../deploy-cloudrun/) action.

## Description

This action removes Cloud Run service traffic tags that were deployed for pull request previews or temporary environments. It's typically used when a pull request is closed or merged.

## Usage

```yaml
name: Cleanup Cloud Run on PR Close

on:
  pull_request:
    types: [closed, unlabeled]

jobs:
  cleanup:
    if: |
      github.event_name == 'pull_request' && 
      ((github.event.action == 'closed' &&
       contains(github.event.pull_request.labels.*.name, 'deploy'))||
       (github.event.action == 'unlabeled' &&
       github.event.label.name == 'deploy'))
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

      - uses: nakamasato/github-actions/cleanup-cloudrun-traffic-tag@main
        with:
          service: 'my-app'
          tag: 'pr-${{ github.event.pull_request.number }}'
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
| `tag` | Traffic tag to remove (e.g., pr-123) | Yes | - |
| `github_token` | GitHub token for PR comments | No | `${{ github.token }}` |

## Outputs

This action does not produce any outputs.

## Requirements

- Google Cloud Platform project with Cloud Run API enabled
- Service account with `roles/run.developer` permission (sufficient for traffic tag management)
- Workload Identity Federation configured for GitHub Actions authentication

## Example Workflow

See the [deploy-cloudrun README](../deploy-cloudrun/README.md) for a complete example that includes both deployment and cleanup actions.
