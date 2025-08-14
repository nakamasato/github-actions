# Build and push to GAR (Google Artifact Registry)

Build a docker image and push it to Google Artifact Registry.

This action uses GitHub Actions cache (GHA cache) for Docker layer caching, which is optimized for Google-hosted runners.

## Inputs

- `project` (required): GCP project id
- `image` (required): Image name
- `workload_identity_provider` (required): Workload Identity Provider
- `service_account` (required): Service Account
- `dockerfile` (optional): Dockerfile path (default: 'Dockerfile')
- `context` (optional): Docker context for build-push-action (default: '.')
- `region` (optional): GCP region (default: 'asia-northeast1')
- `repository` (optional): GCP Artifact Registry repository (default: 'cloud-run-source-deploy')
- `image_tag` (optional): Image tag (default: 'latest')
- `build-args` (optional): Build arguments for docker build
- `driver` (optional): Driver for setup-buildx-action (default: 'docker-container')

## Outputs

- `imageid`: Docker image ID
- `digest`: Image digest
- `metadata`: Image metadata
- `full_image_name`: Full image name (registry/project/repository/image)

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
        uses: nakamasato/github-actions/build-and-push-to-gar@1.13.2
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
