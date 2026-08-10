# Reusable Terraform AWS Workflow

This reusable workflow automates Terraform operations for AWS infrastructure using GitHub Actions.

## Description

A comprehensive workflow that handles Terraform formatting, validation, planning, and deployment for AWS resources. It integrates with AWS IAM roles using OpenID Connect and provides PR comments via tfcmt.

## Usage

```yaml
jobs:
  terraform:
    uses: nakamasato/github-actions/.github/workflows/reusable-terraform-aws.yml@main
    with:
      working_directory: "aws"
      iam_role_plan: "arn:aws:iam::123456789012:role/github-actions-terraform-plan"
      iam_role_apply: "arn:aws:iam::123456789012:role/github-actions-terraform-apply"
      region: "us-east-1"
      identifier: "my-aws-project"
```

## Inputs

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `enable_aqua_cache` | boolean | false | `false` | Enable caching for aqua tool installations |
| `working_directory` | string | false | `"."` | Directory containing Terraform configuration |
| `iam_role` | string | false | - | **(Deprecated)** AWS IAM role ARN. Use `iam_role_plan` and `iam_role_apply` instead |
| `iam_role_plan` | string | false | - | AWS IAM role ARN for terraform plan |
| `iam_role_apply` | string | false | - | AWS IAM role ARN for terraform apply |
| `region` | string | **true** | - | AWS region for operations |
| `identifier` | string | **true** | - | Unique identifier for concurrency control |
| `terraform_version_file` | string | false | `".terraform-version"` | File containing Terraform version (uses 'latest' if not found) |
| `save_tfplan` | boolean | false | `false` | Save Terraform plan as artifact |
| `tfplan_filename` | string | false | `"tfplan.json"` | File name for the plan JSON, also its name inside the artifact (see [Plan artifact layout](#plan-artifact-layout)) |
| `tfplan_retention_days` | number | false | `1` | Number of days to retain Terraform plan artifact |
| `configure_git_credentials` | boolean | false | `false` | Configure git credentials for private modules using GITHUB_TOKEN |

## Outputs

| Name | Description |
|------|-------------|
| `tfplan_artifact_name` | Name of the artifact containing terraform plan JSON |

## Plan artifact layout

By default the artifact holds the plan as `tfplan.json`.

`actions/download-artifact` extracts a **single** artifact directly into `path`
and only nests each artifact under its own name once two or more match. So in a
run where only one stack planned, the artifact-name directory — the only signal
of which stack a plan came from — is gone, and consumers that key per-stack
behaviour off the path fall back to a generic bucket without saying so.

Give the file a stack-specific name so it identifies itself either way:

```yaml
with:
  save_tfplan: true
  tfplan_filename: my-stack.json
```

| Artifacts in the run | Extracted to |
|---|---|
| 1 | `<path>/my-stack.json` |
| 2 or more | `<path>/<artifact-name>/my-stack.json` |

Consumers match both with a `**` glob, e.g. `tfplans/**/my-stack.json`.

## Prerequisites

- AWS IAM role configured with necessary permissions
- OpenID Connect trust relationship between GitHub and AWS
- Repository permissions for `contents: read`, `id-token: write`, and `pull-requests: write`

## Features

- **Terraform Operations**: Format check, initialization, validation, planning, and application
- **AWS Authentication**: Uses OIDC for secure authentication without long-lived credentials
- **PR Comments**: Automatic Terraform plan comments via tfcmt
- **Tool Management**: Automatic installation of aqua and tfcmt
- **Concurrency Control**: Prevents concurrent runs for the same identifier
- **Conditional Apply**: Only applies changes on pushes to main branch

## Example

```yaml
name: AWS Infrastructure

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  terraform:
    uses: nakamasato/github-actions/.github/workflows/reusable-terraform-aws.yml@main
    with:
      working_directory: "terraform/aws"
      iam_role_plan: "arn:aws:iam::123456789012:role/github-actions-terraform-plan"
      iam_role_apply: "arn:aws:iam::123456789012:role/github-actions-terraform-apply"
      region: "us-east-1"
      identifier: "my-project"
      enable_aqua_cache: true
      save_tfplan: true
      tfplan_retention_days: 3
```
