## Prerequisite

[aqua](https://aquaproj.github.io/): tool to manage cli 

Install:

```
brew install aquaproj/aqua/aqua
```

[tfcmt](https://suzuki-shunsuke.github.io/tfcmt/)

```
aqua g -i suzuki-shunsuke/tfcmt
```

## Examples

### GCP

```yaml
name: gcp

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

permissions:
  contents: read
  id-token: write
  pull-requests: write

jobs:
  terraform:
    uses: nakamasato/github-actions/.github/workflows/reusable-terraform-gcp.yml@1.6.5
    with:
      working_directory: <dir>
      project: <project name>
      workload_identity_provider: projects/<project id>/locations/global/workloadIdentityPools/<pool>/providers/<provider>
      service_account: <sa name>@<project name>.iam.gserviceaccount.com
```

### AWS

```yaml
name: aws

on:
  push:
    branches:
      - main
    paths:
      - 'aws/**'
      - .github/workflows/aws.yml
  pull_request:
    branches:
      - main
    paths:
      - 'aws/**'
      - .github/workflows/aws.yml

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      naka: ${{ steps.changes.outputs.naka }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: changes
        with:
          filters: |
            naka:
              - '.github/workflows/aws.yml'
              - 'aws/**'
              - '!aws/**md'

  status-check-aws:
    runs-on: ubuntu-latest
    needs:
      - naka
    permissions: {}
    if: failure()
    steps:
      - run: exit 1

  naka:
    needs: changes
    if: needs.changes.outputs.naka == 'true'
    uses: nakamasato/github-actions/.github/workflows/reusable-terraform-aws.yml@1.4.0
    with:
      working_directory: aws
      iam_role: arn:aws:iam::xxxx:role/github-actions-terraform
      region: ap-northeast-1
      identifier: aws-naka
```
