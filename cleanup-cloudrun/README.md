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
    steps:
      - uses: nakamasato/github-actions/cleanup-cloudrun@main
        with:
          service_name: 'my-app-pr-${{ github.event.pull_request.number }}'
          region: 'us-central1'
          gcp_sa_key: ${{ secrets.GCP_SA_KEY }}
```

## Inputs

| Name | Description | Required | Default |
|------|-------------|----------|---------|
| `service_name` | Name of the Cloud Run service to delete | Yes | - |
| `region` | GCP region where the service is deployed | Yes | - |
| `gcp_sa_key` | Service account key for authentication | Yes | - |

## Outputs

This action does not produce any outputs.

## Requirements

- Google Cloud Platform project with Cloud Run API enabled
- Service account with `roles/run.admin` permission
- The service account key stored as a GitHub secret

## Example Workflow

See the deploy-cloudrun README for a complete example that includes both deployment and cleanup actions.
