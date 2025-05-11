# set-image-tag

This action sets image tag based on GitHub event type:

- pull_request: `pr-<pr number>`
- push: `<branch>-<github short sha>`
- others: `<ref_name>` (release: tag name)

## Inputs

no inputs

## Outputs

- tag

## Usage

```yaml
on:
  pull_request:
  push:
    branches:
      - main
  release:
env:
  APP_NAME: myapp
  PROJECT: myproject
  REGION: asia-northeast1
  WORKLOAD_IDENTITY_PROVIDER: projects/<project_number>/locations/global/workloadIdentityPools/<pool name>/providers/<provider>
  SERVICE_ACCOUNT: github-actions@myproject.iam.gserviceaccount.com
jobs:
  deploy:
    permissions:
      contents: read
      id-token: write
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

      - name: set image tag
        id: set-image-tag
        uses: nakamasato/github-actions/set-image-tag@1.9.0

      - name: Build image and push to GAR
        id: build-and-push
        uses: nakamasato/github-actions/build-and-push-to-gar@1.9.0
        with:
          context: .
          dockerfile: Dockerfile
          project: ${{ env.PROJECT }}
          region: ${{ env.REGION }}
          repository: cloud-run-source-deploy
          image: ${{ env.APP_NAME }}
          image_tag: ${{ steps.set-image-tag.outputs.tag }}
          workload_identity_provider: ${{ env.WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ env.SERVICE_ACCOUNT }}
          build-args: "VERSION=${{ steps.set-config.outputs.IMAGE_TAG }}"

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ${{ env.APP_NAME }} \
            --image ${{ steps.build-and-push.outputs.full_image_name }}:${{ steps.set-image-tag.outputs.tag }} \
            --project ${{ env.PROJECT }} \
            --region ${{ env.REGION }}
```
