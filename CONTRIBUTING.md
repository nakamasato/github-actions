# Contributing to GitHub Actions Repository

Thank you for your interest in contributing to this repository! This guide will help you get started.

## Code of Conduct

By participating in this project, you agree to abide by our code of conduct: be respectful, inclusive, and constructive in all interactions.

## How to Contribute

### Reporting Issues

1. Check if the issue already exists
2. Create a new issue with:
   - Clear title describing the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, versions)
   - Relevant logs or error messages

### Suggesting Features

1. Check existing issues and discussions
2. Open a new issue with:
   - Clear description of the feature
   - Use cases and benefits
   - Potential implementation approach
   - Any alternatives considered

### Contributing Code

#### Prerequisites

- Git and GitHub knowledge
- Familiarity with GitHub Actions
- Node.js 16+ (for JavaScript actions)
- Python 3.12+ (for Python actions)
- Poetry (for Python dependency management)

#### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/github-actions.git
   cd github-actions
   ```

3. Create a feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```

4. Install dependencies:
   ```bash
   # For JavaScript actions
   cd action-name
   npm install
   
   # For Python actions
   cd action-name
   poetry install
   ```

#### Making Changes

1. Follow the [action creation guide](docs/creating-new-action.md)
2. Adhere to [best practices](docs/best-practices.md)
3. Write tests following [testing guidelines](docs/testing-guidelines.md)
4. Update documentation as needed

#### Commit Guidelines

We follow conventional commits:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Examples:
```bash
git commit -m "feat: add timeout option to deploy action"
git commit -m "fix: handle spaces in file paths"
git commit -m "docs: update README with new examples"
```

#### Pull Request Process

1. Ensure all tests pass locally
2. Update documentation if needed
3. Push your branch and create a PR
4. Fill out the PR template completely
5. Link related issues
6. Wait for review and address feedback

#### PR Checklist

- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] PR description is clear
- [ ] Related issues are linked

### Testing

Before submitting:

```bash
# JavaScript actions
npm test
npm run lint

# Python actions
poetry run pytest
poetry run ruff check .
poetry run ruff format --check .
```

### Documentation

- Update README.md for user-facing changes
- Add JSDoc/docstrings for new functions
- Include examples for new features
- Keep documentation concise and clear

## Development Guidelines

### Code Style

#### JavaScript
- Use ES6+ features
- 2 spaces for indentation
- Single quotes for strings
- No semicolons (StandardJS)

#### Python
- Follow PEP 8
- Use type hints
- Format with ruff
- Write docstrings for public functions

### Action Structure

All actions should follow the standard structure:
```
action-name/
├── action.yml
├── README.md
├── src/
├── tests/
├── examples/
└── .github/
```

### Testing Requirements

- Minimum 80% code coverage
- Test happy paths and edge cases
- Include integration tests
- Mock external dependencies

## Review Process

### What We Look For

1. **Code Quality**: Clean, readable, maintainable
2. **Testing**: Comprehensive test coverage
3. **Documentation**: Clear and complete
4. **Performance**: Efficient implementation
5. **Security**: No vulnerabilities introduced

### Review Timeline

- Initial review: 2-3 business days
- Follow-up reviews: 1-2 business days
- Complex features may take longer

## Release Process

1. Maintainers merge PR to main
2. Create release with semantic versioning
3. Update major version tags
4. Publish to GitHub Marketplace (if applicable)

## Getting Help

- Check [documentation](docs/)
- Review existing [issues](https://github.com/nakamasato/github-actions/issues)
- Ask questions in [discussions](https://github.com/nakamasato/github-actions/discussions)
- Tag maintainers for urgent issues

## Recognition

Contributors will be:
- Listed in release notes
- Added to contributors list
- Thanked in pull request comments

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing! 🎉