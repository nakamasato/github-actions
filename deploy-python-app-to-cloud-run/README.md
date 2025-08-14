# deploy-python-app-to-cloud-run

## Description

Deploy Python app with https://buildpacks.io/ (using `heroku/builder:22`) or Docker build-push-action.

This action uses GitHub Actions cache (GHA cache) for Docker layer caching when using Dockerfile builds, which is optimized for Google-hosted runners.

## Prerequisite

You need to create Workload Identity Provider (https://cloud.google.com/iam/docs/workload-identity-federation) and Service Account with sufficient permissions (e.g. `roles/iam.workloadIdentityUser`, `roles/artifactregistry.writer`, `roles/run.developer`).

For more details about setting

## inputs

1. `project` (required): GCP project id
1. `region` (optional): GCP region (default `asia-northeast1`)
1. `verbosity` (optional): Cloud Run deploy command verbosity (default `warning`)
1. `service` (required): Cloud Run service name
1. `repository` (optional): GCP Artifact Registry repository (default `cloud-run-source-deploy`)
1. `image` (required): image name
1. `image_tag` (optional): image tag (default `latest`)
1. `workload_identity_provider` (required): workload identity provider
1. `service_account` (required): service account
1. `dockerfile` (optional): Dockerfile path for build-push-action (default: use buildpacks)
1. `context` (optional): Docker context for build-push-action (default `.`)
1. `build-args` (optional): Build arguments for docker build
1. `driver` (optional): Driver for setup-buildx-action (default `docker-container`)

## outputs

1. `url`: Cloud Run URL

## Example1: Build with buildpacks

```yaml
name: deploy-cloudrun
on:
  pull_request:

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

      - name: Set up Python & Poetry
        uses: nakamasato/github-actions/setup-poetry@1.6.0
        with:
          install-dependencies: false

      - name: Set tag
        id: set-tag
        run: |
          echo "IMAGE_TAG=${{ github.event_name == 'pull_request' && github.sha || github.ref_name }}" >> "$GITHUB_OUTPUT"

      - name: Deploy CloudRun
        uses: nakamasato/github-actions/deploy-python-app-to-cloud-run@1.13.2
        with:
          project: ${{ env.PROJECT }}
          region: ${{ env.REGION }}
          service: ${{ env.CLOUD_RUN_SERVICE }}
          repository: ${{ env.REPOSITORY }}
          image: ${{ env.IMAGE }}
          image_tag: ${{ steps.set-tag.outputs.IMAGE_TAG }}
          workload_identity_provider: ${{ env.WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ env.SERVICE_ACCOUNT }}
```

## Example1: Build with [build-push-action](https://github.com/docker/build-push-action)

```yaml
name: deploy-cloudrun
on:
  pull_request:

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

      - name: Set up Python & Poetry
        uses: nakamasato/github-actions/setup-poetry@1.6.0
        with:
          install-dependencies: false

      - name: Set tag
        id: set-tag
        run: |
          echo "IMAGE_TAG=${{ github.event_name == 'pull_request' && github.sha || github.ref_name }}" >> "$GITHUB_OUTPUT"

      - name: Deploy CloudRun
        uses: nakamasato/github-actions/deploy-python-app-to-cloud-run@1.13.2
        with:
          dockerfile: Dockerfile # this is necessary to use build-push-actions
          context: . # optional config for build-push-actions
          project: ${{ env.PROJECT }}
          region: ${{ env.REGION }}
          service: ${{ env.CLOUD_RUN_SERVICE }}
          repository: ${{ env.REPOSITORY }}
          image: ${{ env.IMAGE }}
          image_tag: ${{ steps.set-tag.outputs.IMAGE_TAG }}
          workload_identity_provider: ${{ env.WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ env.SERVICE_ACCOUNT }}
```
