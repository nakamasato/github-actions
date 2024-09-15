# deploy-python-app-to-cloud-run

## inputs

1. `project`: GCP project id
2. `region`: GCP region (default `asia-northeast1`)
3. `service`: Cloud Run service name
4. `repository`: GCP Artifact Registry repository
5. `image`: image name
6. `image_tag`: image tag
7. `workload_identity_provider`: workload identity provider
8. `service_account`: service account

## outputs

1. `url`: Cloud Run URL

## Example

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
      contents: write # create tag
      pull-requests: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python & Poetry
        uses: nakamasato/github-actions/setup-poetry@1.5.0
        with:
          version: 1.8.2
          install-dependencies: false

      - name: Set tag
        id: set-tag
        run: |
          echo "IMAGE_TAG=${{ github.event_name == 'pull_request' && github.sha || github.ref_name }}" >> "$GITHUB_OUTPUT"

      - name: Deploy CloudRun
        uses: nakamasato/github-actions/deploy-python-app-to-cloud-run@1.5.0
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
