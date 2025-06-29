# Testing Guidelines

This document outlines testing best practices for GitHub Actions in this repository.

## Testing Philosophy

- **Test Early, Test Often**: Write tests as you develop
- **Comprehensive Coverage**: Test both happy paths and edge cases
- **Fast Feedback**: Tests should run quickly
- **Isolated Tests**: Each test should be independent

## Testing Strategies by Action Type

### Composite Actions

Composite actions are challenging to unit test directly. Focus on:

1. **Integration Testing**: Test the entire action in a workflow
2. **Component Testing**: Test individual shell scripts separately
3. **Mock External Dependencies**: Use test doubles for external services

### JavaScript Actions

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test the complete action
3. **Mocking**: Mock `@actions/core` and `@actions/github`

Example test structure:
```javascript
// index.test.js
const core = require('@actions/core');
const github = require('@actions/github');
const { run } = require('./index');

jest.mock('@actions/core');
jest.mock('@actions/github');

describe('Action Name', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should complete successfully', async () => {
    // Setup
    core.getInput.mockReturnValueOnce('test-value');
    
    // Execute
    await run();
    
    // Assert
    expect(core.setOutput).toHaveBeenCalledWith('result', 'expected');
  });
});
```

### Python Actions

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test the complete action flow
3. **Fixtures**: Use pytest fixtures for common test data

Example test structure:
```python
# test_main.py
import pytest
from unittest.mock import patch, MagicMock
from src.main import run

@pytest.fixture
def mock_github_context():
    return {
        'repository': 'owner/repo',
        'pull_request': {'number': 123}
    }

def test_action_success(mock_github_context):
    with patch.dict('os.environ', {'INPUT_TOKEN': 'fake-token'}):
        with patch('src.main.github') as mock_github:
            # Setup
            mock_github.get_pull_request.return_value = MagicMock()
            
            # Execute
            result = run()
            
            # Assert
            assert result == 'expected'
```

## Testing Tools

### Workflow Validation
- **actionlint**: Static analysis for GitHub Actions workflows
- Catches syntax errors, missing inputs, and workflow issues
- Integrates with CI/CD for automatic validation

### JavaScript
- **Jest**: Primary testing framework
- **nock**: HTTP request mocking
- **@actions/github**: GitHub API client mocking

### Python
- **pytest**: Primary testing framework
- **pytest-cov**: Coverage reporting
- **responses**: HTTP request mocking
- **unittest.mock**: Built-in mocking

## CI/CD Testing

### Test Matrix

Use GitHub Actions matrix strategy to test across:
- Multiple OS: `ubuntu-latest`, `windows-latest`, `macos-latest`
- Multiple versions of Node.js/Python
- Different action input combinations

Example:
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    node: [16, 18, 20]
```

### Test Workflows

Create `.github/workflows/test-{action-name}.yml`:

```yaml
name: Test Action Name

on:
  push:
    paths:
      - 'action-name/**'
      - '.github/workflows/test-action-name.yml'
  pull_request:
    paths:
      - 'action-name/**'

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      
      - name: Run unit tests
        run: |
          cd action-name
          npm test  # or poetry run pytest
      
      - name: Test action
        uses: ./action-name
        with:
          test-input: 'value'
```

## Coverage Requirements

- Minimum coverage: 80%
- Critical paths: 100%
- New code: 90%

## Test Data Management

1. **Fixtures**: Store test data in `tests/fixtures/`
2. **Secrets**: Never commit real secrets, use test values
3. **Large Files**: Use git-lfs or generate programmatically

## Performance Testing

For actions that may run frequently:
1. Measure execution time
2. Profile memory usage
3. Test with large inputs
4. Ensure graceful degradation

## Security Testing

1. Test input validation
2. Verify secret handling
3. Check for injection vulnerabilities
4. Test permission boundaries

## Debugging Tests

### Local Testing

1. **act**: Run GitHub Actions locally
   ```bash
   act -j test
   ```

2. **Debug Logging**: Enable debug logs
   ```bash
   ACTIONS_STEP_DEBUG=true npm test
   ```

### CI Debugging

1. Use `actions/upload-artifact` to save test outputs
2. Enable debug logging in workflows
3. Use `tmate` for interactive debugging

## Best Practices

1. **Descriptive Names**: Test names should explain what they test
2. **Arrange-Act-Assert**: Structure tests clearly
3. **DRY**: Extract common setup to helpers/fixtures
4. **Fast Tests**: Mock external dependencies
5. **Deterministic**: Tests should not be flaky
6. **Documentation**: Comment complex test logic

## Common Pitfalls

1. **Environment Dependencies**: Tests should not depend on local environment
2. **Test Interdependence**: Each test should run independently
3. **Over-mocking**: Don't mock what you're testing
4. **Ignoring Edge Cases**: Test error conditions
5. **Slow Tests**: Keep individual tests under 5 seconds

## Continuous Improvement

1. Regular test review and refactoring
2. Monitor test execution times
3. Track and improve coverage
4. Update tests when fixing bugs
5. Learn from test failures