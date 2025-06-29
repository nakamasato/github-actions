# Creating a New Action

This guide will help you create a new GitHub Action in this repository.

## Action Types

We support three types of actions:

1. **Composite Actions** - Combine multiple steps into a single action
2. **JavaScript Actions** - Actions written in JavaScript/TypeScript
3. **Python Actions** - Actions written in Python

## Directory Structure

All actions should follow this standard structure:

```
action-name/
├── action.yml         # Action metadata and inputs/outputs
├── README.md          # Detailed documentation
├── src/               # Source code (if applicable)
├── tests/             # Test files
├── examples/          # Usage examples
└── .github/           # Action-specific workflows (optional)
```

## Step-by-Step Guide

### 1. Choose Your Action Type

Decide whether your action will be:
- **Composite**: Best for combining existing actions/commands
- **JavaScript**: Best for Node.js-based logic with fast startup
- **Python**: Best for complex logic or when using Python libraries

### 2. Create the Action Directory

```bash
mkdir -p your-action-name/{src,tests,examples}
```

### 3. Create action.yml

Every action needs an `action.yml` file. Use the appropriate template:

- [Composite Action Template](../templates/composite-action/action.yml)
- [JavaScript Action Template](../templates/javascript-action/action.yml)
- [Python Action Template](../templates/python-action/action.yml)

### 4. Write Your Action Logic

#### For Composite Actions
- Define steps in `action.yml`
- Use `shell` to specify the shell for run steps
- Reference inputs with `${{ inputs.input-name }}`

#### For JavaScript Actions
- Create `src/index.js` as your entry point
- Use `@actions/core` and `@actions/github` packages
- Build distributable with `ncc` or similar

#### For Python Actions
- Create `src/main.py` as your entry point
- Use `poetry` for dependency management
- Include `pyproject.toml` for dependencies

### 5. Add Tests

- **JavaScript**: Use Jest for testing
- **Python**: Use pytest for testing
- Include both unit tests and integration tests

### 6. Create Documentation

Your `README.md` should include:
- Description of what the action does
- Input/output documentation
- Usage examples
- Prerequisites
- Troubleshooting guide

### 7. Add Examples

Create example workflows in `examples/`:
- Basic usage example
- Advanced usage with all options
- Integration with other actions

### 8. Test Your Action

1. Create a test workflow in `.github/workflows/`
2. Test locally using [act](https://github.com/nektos/act) if possible
3. Push to a branch and test in a real workflow

## Best Practices

1. **Naming**: Use kebab-case for action names
2. **Versioning**: Follow semantic versioning
3. **Inputs**: Provide sensible defaults where possible
4. **Outputs**: Only output what's necessary
5. **Error Handling**: Fail gracefully with helpful error messages
6. **Logging**: Use appropriate log levels (debug, info, warning, error)
7. **Documentation**: Keep README up-to-date with changes

## Testing Checklist

- [ ] Action runs successfully with minimal inputs
- [ ] Action handles all edge cases gracefully
- [ ] Action fails appropriately on invalid inputs
- [ ] Documentation is clear and complete
- [ ] Examples work as documented
- [ ] Tests pass in CI/CD pipeline

## Publishing

1. Ensure all tests pass
2. Update version in relevant files
3. Create a pull request
4. After merge, create a release with appropriate tag

## Need Help?

- Check existing actions for examples
- Review [GitHub Actions documentation](https://docs.github.com/en/actions)
- Open an issue for questions or suggestions