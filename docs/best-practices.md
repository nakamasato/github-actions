# GitHub Actions Best Practices

This guide contains best practices for developing GitHub Actions in this repository.

## General Principles

1. **Single Responsibility**: Each action should do one thing well
2. **Idempotency**: Running an action multiple times should produce the same result
3. **Fail Fast**: Detect and report errors as early as possible
4. **Clear Communication**: Provide helpful error messages and logs

## Action Design

### Inputs and Outputs

#### Inputs
- Use clear, descriptive names (kebab-case)
- Provide sensible defaults where possible
- Validate inputs early in execution
- Document all inputs in action.yml and README

```yaml
inputs:
  file-path:
    description: 'Path to the file to process'
    required: true
  verbose:
    description: 'Enable verbose logging'
    required: false
    default: 'false'
```

#### Outputs
- Only output what's necessary
- Use consistent naming conventions
- Document output format and possible values

```yaml
outputs:
  result:
    description: 'The processed result'
  status:
    description: 'Success or failure status'
```

### Error Handling

1. **Validate Early**: Check inputs before processing
2. **Graceful Failures**: Provide context when failing
3. **Exit Codes**: Use appropriate exit codes
4. **Recovery**: Attempt recovery where sensible

```javascript
// Good error handling
try {
  validateInputs(inputs);
  const result = await processData(inputs);
  core.setOutput('result', result);
} catch (error) {
  core.setFailed(`Action failed: ${error.message}`);
  if (error.stack && core.isDebug()) {
    core.debug(error.stack);
  }
}
```

### Logging

Use appropriate log levels:
- **Debug**: Detailed information for troubleshooting
- **Info**: General information about execution
- **Warning**: Non-critical issues
- **Error**: Critical problems

```javascript
core.debug('Detailed processing information');
core.info('Processing file: ' + filePath);
core.warning('Using deprecated option');
core.error('Failed to process file');
```

## Performance Optimization

### Startup Time
- Minimize dependencies
- Use compiled/bundled code for JavaScript
- Cache dependencies in CI

### Execution Time
- Process data efficiently
- Use parallelization where appropriate
- Set reasonable timeouts

### Resource Usage
- Clean up temporary files
- Limit memory consumption
- Be mindful of API rate limits

## Security Best Practices

### Secrets Management
- Never log secrets
- Use GitHub's secret masking
- Validate secret format
- Rotate secrets regularly

```javascript
// Bad: Logging secrets
console.log(`Token: ${token}`);

// Good: Using secret masking
core.setSecret(token);
core.info('Using provided authentication token');
```

### Input Validation
- Sanitize all inputs
- Prevent injection attacks
- Validate file paths
- Check permissions

```python
# Validate file paths
def validate_path(path):
    # Ensure path is within workspace
    abs_path = os.path.abspath(path)
    workspace = os.path.abspath(os.environ['GITHUB_WORKSPACE'])
    if not abs_path.startswith(workspace):
        raise ValueError('Path must be within workspace')
    return abs_path
```

### Dependencies
- Keep dependencies up-to-date
- Audit for vulnerabilities
- Pin dependency versions
- Use lockfiles

## Code Quality

### Workflow Validation
- **actionlint**: Static analysis for GitHub Actions workflows
- Validates workflow syntax and logic
- Catches common mistakes and suggests improvements
- Runs automatically on workflow file changes

### Linting and Formatting

#### JavaScript
- ESLint with standard configuration
- Prettier for formatting

#### Python
- Ruff for linting and formatting
- Type hints where appropriate

### Code Structure
- Keep files focused and small
- Extract reusable functions
- Use meaningful variable names
- Comment complex logic

### Testing
- Write tests first (TDD)
- Maintain high coverage
- Test edge cases
- Use continuous integration

## Documentation

### README Structure
1. **Description**: What the action does
2. **Usage**: Basic example
3. **Inputs**: All inputs with descriptions
4. **Outputs**: All outputs with descriptions
5. **Examples**: Multiple use cases
6. **Requirements**: Prerequisites
7. **Troubleshooting**: Common issues

### Inline Documentation
- Document complex algorithms
- Explain non-obvious decisions
- Keep comments up-to-date
- Use JSDoc/docstrings

## Versioning

### Semantic Versioning
- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes

### Release Process
1. Update version in package.json/pyproject.toml
2. Update CHANGELOG
3. Create git tag
4. Create GitHub release
5. Update major version tag

```bash
# After releasing v1.2.3
git tag -fa v1 -m "Update v1 tag"
git push origin v1 --force
```

## Compatibility

### OS Compatibility
- Test on Ubuntu, Windows, and macOS
- Handle path separators correctly
- Be aware of shell differences

### GitHub Runner Versions
- Test on different runner versions
- Document minimum requirements
- Handle missing tools gracefully

## Monitoring and Maintenance

### Action Analytics
- Monitor usage patterns
- Track failure rates
- Measure performance
- Collect user feedback

### Regular Maintenance
- Update dependencies monthly
- Review and update documentation
- Refactor based on usage patterns
- Archive deprecated actions

## Anti-Patterns to Avoid

1. **Doing Too Much**: Keep actions focused
2. **Poor Error Messages**: Always provide context
3. **Hardcoding Values**: Use inputs for configuration
4. **Ignoring Edge Cases**: Handle all scenarios
5. **Missing Tests**: Always include tests
6. **Sparse Documentation**: Document thoroughly
7. **Breaking Changes**: Use semantic versioning
8. **Security Shortcuts**: Never compromise security

## Examples of Well-Designed Actions

### Good: Clear, Focused Action
```yaml
name: 'Upload to S3'
description: 'Upload files to Amazon S3 bucket'
inputs:
  files:
    description: 'Files to upload (glob pattern)'
    required: true
  bucket:
    description: 'S3 bucket name'
    required: true
  prefix:
    description: 'S3 key prefix'
    required: false
    default: ''
outputs:
  uploaded-files:
    description: 'List of uploaded file URLs'
```

### Bad: Unfocused, Complex Action
```yaml
name: 'Do Everything'
description: 'Build, test, deploy, and more'
inputs:
  what-to-do:
    description: 'What should this action do?'
  maybe-deploy:
    description: 'Deploy if you want'
  # 20 more vague inputs...
```

## Conclusion

Following these best practices will help create reliable, maintainable, and user-friendly GitHub Actions. Always prioritize clarity, security, and user experience in your action development.