# Reusable Terraform GCP Workflow

This reusable workflow automates Terraform operations for Google Cloud Platform infrastructure using GitHub Actions.

## Description

A comprehensive workflow that handles Terraform formatting, validation, planning, and deployment for GCP resources. It integrates with Google Cloud using Workload Identity Federation and provides PR comments via tfcmt.

## Usage

```yaml
jobs:
  terraform:
    uses: nakamasato/github-actions/.github/workflows/reusable-terraform-gcp.yml@main
    with:
      working_directory: "gcp"
      project: "my-gcp-project"
      workload_identity_provider: "projects/123456789012/locations/global/workloadIdentityPools/my-pool/providers/my-provider"
      service_account: "terraform@my-gcp-project.iam.gserviceaccount.com"
```

## Inputs

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `working_directory` | string | false | `"."` | Directory containing Terraform configuration |
| `enable_aqua_cache` | boolean | false | `false` | Enable caching for aqua tool installations |
| `project` | string | **true** | - | GCP project name for concurrency control |
| `terraform_version_file` | string | false | `".terraform-version"` | File containing Terraform version (uses 'latest' if not found) |
| `workload_identity_provider` | string | **true** | - | GCP Workload Identity Provider resource name |
| `service_account` | string | **true** | - | GCP service account email for authentication |

## Outputs

This workflow does not produce outputs.

## Prerequisites

- GCP project with Workload Identity Federation configured
- Service account with necessary permissions for Terraform operations
- Repository permissions for `contents: read`, `id-token: write`, and `pull-requests: write`

## Features

- **Terraform Operations**: Format check, initialization, validation, planning, and application
- **GCP Authentication**: Uses Workload Identity Federation for secure authentication
- **PR Comments**: Automatic Terraform plan comments via tfcmt
- **Tool Management**: Automatic installation of aqua and tfcmt
- **Concurrency Control**: Prevents concurrent runs for the same project
- **Conditional Apply**: Only applies changes on pushes to main branch

## Example

```yaml
name: GCP Infrastructure

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  id-token: write
  pull-requests: write

jobs:
  terraform:
    uses: nakamasato/github-actions/.github/workflows/reusable-terraform-gcp.yml@main
    with:
      working_directory: "terraform/gcp"
      project: "my-gcp-project"
      workload_identity_provider: "projects/123456789012/locations/global/workloadIdentityPools/my-pool/providers/my-provider"
      service_account: "terraform@my-gcp-project.iam.gserviceaccount.com"
      enable_aqua_cache: true
```