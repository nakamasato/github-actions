# Action Name

Brief description of what this action does and why it's useful.

## Usage

```yaml
- uses: owner/repo/action-name@v1
  with:
    example-input: 'value'
    optional-input: 'another-value'
```

## Inputs

| Name | Description | Required | Default |
|------|-------------|----------|---------|
| `example-input` | Description of this input | Yes | `default-value` |
| `optional-input` | An optional input parameter | No | - |

## Outputs

| Name | Description |
|------|-------------|
| `result` | Description of the output |

## Examples

### Basic Usage

```yaml
name: Example Workflow

on: [push]

jobs:
  example:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run action
        id: action
        uses: owner/repo/action-name@v1
        with:
          example-input: 'my-value'
      
      - name: Use output
        run: echo "Result: ${{ steps.action.outputs.result }}"
```

### Advanced Usage

```yaml
name: Advanced Example

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  advanced:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run action with all options
        uses: owner/repo/action-name@v1
        with:
          example-input: ${{ github.event.pull_request.number }}
          optional-input: 'custom-value'
```

## Requirements

- Runs on: Ubuntu, macOS, Windows
- Requires: Bash shell

## Troubleshooting

### Common Issues

1. **Error: example-input is required**
   - Ensure you're providing the required input
   - Check for typos in the input name

2. **Permission denied**
   - Make sure the workflow has necessary permissions
   - Check repository settings

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for development guidelines.

## License

[License information]