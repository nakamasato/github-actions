# Reusable GitHub Actions

A collection of reusable GitHub Actions and workflows to streamline your CI/CD pipelines.

## 🏗️ CI/CD Actions

Actions for building, testing, and deploying applications:

- **[build-and-push-to-gar](build-and-push-to-gar)** - Build and push Docker images to Google Artifact Registry
- **[deploy-python-app-to-cloud-run](deploy-python-app-to-cloud-run)** - Deploy Python applications to Google Cloud Run
- **[set-image-tag](set-image-tag)** - Generate consistent image tags for deployments

## 🛠️ Development Tools

Actions to enhance your development workflow:

- **[setup-poetry](setup-poetry)** - Set up Python Poetry for dependency management
- **[llm-pr-reviewer](llm-pr-reviewer)** - AI-powered code review using Large Language Models
- **[pr-description-writer](pr-description-writer)** - Automatically generate PR descriptions

## 🏗️ Infrastructure as Code

[Reusable Workflows](https://docs.github.com/en/actions/sharing-automations/reusing-workflows) for infrastructure management:

- **[reusable-terraform-aws](https://github.com/nakamasato/github-actions/blob/main/.github/workflows/reusable-terraform-aws.yml)** - Terraform workflow for AWS resources
- **[reusable-terraform-gcp](https://github.com/nakamasato/github-actions/blob/main/.github/workflows/reusable-terraform-gcp.yml)** - Terraform workflow for Google Cloud Platform
- **[reusable-terraform-github](https://github.com/nakamasato/github-actions/blob/main/.github/workflows/reusable-terraform-github.yml)** - Terraform workflow for GitHub resources

## 📚 Documentation

- **[Creating New Actions](docs/creating-new-action.md)** - Step-by-step guide for adding new actions
- **[Testing Guidelines](docs/testing-guidelines.md)** - Best practices for testing actions
- **[Best Practices](docs/best-practices.md)** - Development guidelines and conventions
- **[Architecture Overview](ARCHITECTURE.md)** - Repository structure and design principles
- **[Contributing](CONTRIBUTING.md)** - How to contribute to this repository

## 🚀 Quick Start

1. **Browse Actions**: Check the categories above to find the action you need
2. **View Examples**: Each action includes usage examples in its `examples/` directory
3. **Copy & Customize**: Use the provided examples as starting points
4. **Create New Actions**: Use our [templates](templates/) to create new actions

## 🧪 Testing

All actions include comprehensive test suites and are validated through CI/CD pipelines.

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

## 📄 License

This project is licensed under the MIT License - see individual action directories for specific license information.
