# setup-poetry

## Description

Install Python and poetry with versions from `.tool-versions` and `.python-version`.

## inputs

1. `version` (optional): poetry version. default is `latest`. if you have `.tool-versions`, the poetry version is taken from the file.
1. `install-dependencies` (optional): whether to run `poetry install`. default is `true`.

## outputs

no outputs

## Examples

```yaml
name: python
on:
  push:
    branches:
      - main
  pull_request:
  release:
    types: [published]

concurrency:
  group: ${{ github.ref }}
  cancel-in-progress: true

env:
  COMMENT_BODY_IDENTIFIER: Pytest Coverage Comment

permissions:
  contents: read
  pull-requests: write

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false

      - name: Set up Python & Poetry
        uses: nakamasato/github-actions/setup-poetry@1.6.0

      - name: test
        run: |
          set -o pipefail
          poetry run pytest | tee pytest-coverage.txt
```
