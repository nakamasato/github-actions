# deploy-python-app-to-cloud-run

## Description

Deploy Python app with https://buildpacks.io/ (using `heroku/builder:22`)

## Prerequisite

You need to create Workload Identity Provider (https://cloud.google.com/iam/docs/workload-identity-federation) and Service Account with sufficient permissions (e.g. `roles/iam.workloadIdentityUser`, `roles/artifactregistry.writer`, `roles/run.developer`).

For more details about setting 

## inputs

1. `project` (required): GCP project id
1. `region` (optional): GCP region (default `asia-northeast1`)
1. `service` (required): Cloud Run service name
1. `repository` (required): GCP Artifact Registry repository
1. `image` (required): image name
1. `image_tag` (required): image tag
1. `workload_identity_provider` (required): workload identity provider
1. `service_account` (required): service account

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
        uses: nakamasato/github-actions/deploy-python-app-to-cloud-run@1.8.0
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
        uses: nakamasato/github-actions/deploy-python-app-to-cloud-run@1.8.0
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

