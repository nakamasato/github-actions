# Reusable Terraform GitHub Workflow

This reusable workflow automates Terraform operations for GitHub resources using GitHub Actions.

## Description

A comprehensive workflow that handles Terraform formatting, validation, planning, and deployment for GitHub resources. It supports both GitHub App authentication and optional GCP backend storage via Workload Identity Federation.

## Usage

```yaml
jobs:
  terraform:
    uses: nakamasato/github-actions/.github/workflows/reusable-terraform-github.yml@main
    with:
      working_directory: "github"
      project: "my-github-project"
      workload_identity_provider: "projects/123456789012/locations/global/workloadIdentityPools/my-pool/providers/my-provider"
      service_account: "terraform@my-gcp-project.iam.gserviceaccount.com"
    secrets:
      gh_app_id: ${{ secrets.GH_APP_ID }}
      gh_private_key: ${{ secrets.GH_PRIVATE_KEY }}
```

## Inputs

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `enable_aqua_cache` | boolean | false | `false` | Enable caching for aqua tool installations |
| `working_directory` | string | false | `"."` | Directory containing Terraform configuration |
| `project` | string | false | `"github"` | Project name for concurrency control |
| `workload_identity_provider` | string | false | - | GCP Workload Identity Provider (for GCS backend) |
| `service_account` | string | false | - | GCP service account email (for GCS backend) |
| `terraform_version_file` | string | false | `".terraform-version"` | File containing Terraform version (uses 'latest' if not found) |

## Secrets

| Name | Required | Description |
|------|----------|-------------|
| `gh_app_id` | **true** | GitHub App ID for authentication |
| `gh_private_key` | **true** | GitHub App private key for authentication |

## Outputs

This workflow does not produce outputs.

## Prerequisites

- GitHub App with necessary permissions for managing GitHub resources
- Repository permissions for `contents: read`, `id-token: write`, and `pull-requests: write`
- Optional: GCP project with Workload Identity Federation for backend storage

## Features

- **Terraform Operations**: Format check, initialization, validation, planning, and application
- **GitHub App Authentication**: Uses GitHub App for secure GitHub provider operations
- **GCS Backend Support**: Optional Google Cloud Storage backend for state management
- **PR Comments**: Automatic Terraform plan comments via tfcmt
- **Tool Management**: Automatic installation of aqua and tfcmt
- **Concurrency Control**: Prevents concurrent runs for the same project
- **Conditional Apply**: Only applies changes on pushes to main branch

## Example

```yaml
name: GitHub Infrastructure

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  id-token: write
  pull-requests: write
  issues: write

jobs:
  terraform:
    uses: nakamasato/github-actions/.github/workflows/reusable-terraform-github.yml@main
    with:
      working_directory: "terraform/github"
      project: "my-github-project"
      workload_identity_provider: "projects/123456789012/locations/global/workloadIdentityPools/my-pool/providers/my-provider"
      service_account: "terraform@my-gcp-project.iam.gserviceaccount.com"
      enable_aqua_cache: true
    secrets:
      gh_app_id: ${{ secrets.GH_APP_ID }}
      gh_private_key: ${{ secrets.GH_PRIVATE_KEY }}
```