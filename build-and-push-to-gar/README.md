# Build and push to GAR (Google Artifact Registry)

## Inputs

- dockerfile
- context
- region
- repository
- image
- image_tag
- workload_identity_provider
- service_account

## Outputs

- imageid
- digest
- metadata

## Example

```yaml
name: deploy-cloudrun
on:
  pull_request:
  push:
    branches:
      - main

env:
  PROJECT: <your project>
  REGION: asia-northeast1
  WORKLOAD_IDENTITY_PROVIDER: projects/<project_number>/locations/global/workloadIdentityPools/<pool>/providers/<provider>
  SERVICE_ACCOUNT: <sa name>@<project name>.iam.gserviceaccount.com
  IMAGE: <image name>
  CLOUD_RUN_SERVICE: <cloud run service name>
  REPOSITORY: <repository name e.g. cloud-run-source-deploy>

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
      pull-requests: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Build and Push
        uses: nakamasato/github-actions/build-and-push-to-gar@1.8.0
        with:
          dockerfile: Dockerfile
          context: . # optional config for build-push-actions
          project: ${{ env.PROJECT }}
          region: ${{ env.REGION }}
          repository: ${{ env.REPOSITORY }}
          image: ${{ env.IMAGE }}
          image_tag: ${{ github.event_name == 'pull_request' && format('pr-{0}', github.event.number) || format('{0}-{1}', github.ref_name, github.sha) }}
          workload_identity_provider: ${{ env.WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ env.SERVICE_ACCOUNT }}
```
