# PR Description Writer

A GitHub Action that automatically generates Pull Request titles and descriptions based on code changes.

## Features

- Analyzes changed files in a PR to understand the code changes
- Uses OpenAI or Anthropic LLMs to generate meaningful PR descriptions
- Supports custom PR templates
- Can learn from example PRs to match your team's style
- Allows custom prompt instructions

## Usage

Add this action to your GitHub workflow:

```yaml
name: Generate PR Description

on:
  pull_request:
    types: [opened, synchronize]
    branches: [ main, master ]

jobs:
  generate-description:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate PR Description
        uses: yourusername/pr-description-writer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          llm_provider: 'anthropic'  # or 'openai'
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          anthropic_model: 'claude-3-opus-20240229'
          # Optional parameters
          # prs: 'https://github.com/org/repo/pull/1,https://github.com/org/repo/pull/2'
          # pull_request_template_path: '.github/custom_template.md'
          # prompt_path: '.github/pr_prompt.txt'
```

## Inputs

| Input                       | Description                                           | Required | Default                           |
|-----------------------------|-------------------------------------------------------|----------|-----------------------------------|
| `github_token`              | GitHub token for API access                           | Yes      | N/A                               |
| `llm_provider`              | LLM provider to use ('openai' or 'anthropic')         | Yes      | N/A                               |
| `openai_api_key`            | OpenAI API key (required if using OpenAI)             | No       | N/A                               |
| `openai_model`              | OpenAI model to use                                   | No       | `gpt-4-turbo`                     |
| `anthropic_api_key`         | Anthropic API key (required if using Anthropic)       | No       | N/A                               |
| `anthropic_model`           | Anthropic model to use                                | No       | `claude-3-opus-20240229`          |
| `prs`                       | Comma-separated list of example PR URLs               | No       | `""`                              |
| `pull_request_template_path`| Path to PR template file                              | No       | `.github/pull_request_template.md`|
| `prompt_path`               | Path to custom prompt file                            | No       | `""`                              |

## Custom Prompts

You can create a custom prompt file to guide how the LLM should fill out your PR template. For example:

```
Please follow these guidelines when generating the PR description:
1. Focus on the "why" rather than the "what" (the code changes already show what was changed)
2. Mention any performance improvements
3. List any breaking changes prominently
4. Use bullet points for listing changes
```

## Example PR Template

This action works best when you have a structured PR template:

```markdown
## What does this PR do?

<!-- Brief description of what this PR does -->

## Why was this change made?

<!-- Explain the context and motivation for this change -->

## What changes were made?

<!-- Technical details about the implementation -->

## Testing

<!-- How was this change tested? -->

## Screenshots (if applicable)

<!-- Add screenshots here -->

## Related Issues

<!-- Link to related issues here -->
```

## Building the Action

```bash
npm install
npm run build
```

## License

MIT
