# LLM PR Reviewer

A GitHub Action that automatically reviews Pull Requests and adds helpful code improvement suggestions as comments using an LLM (Large Language Model).

## Features

- Analyzes code changes in PRs and suggests improvements
- Comments directly on the specific lines that need attention
- Provides context-aware suggestions by examining referenced files
- Customizable file extensions and exclusion patterns
- Limits the number of comments to avoid overwhelming reviewers
- Suggests improvements with explanatory comments and code suggestions

## Setup

### Create a workflow file

Create a file named `.github/workflows/pr-review.yml` in your repository:

```yaml
name: PR Code Review

on:
  pull_request:
    types: [opened, synchronize]
    
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: LLM PR Reviewer
        uses: your-username/llm-pr-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          # Optional configurations:
          # file_extensions: ".js,.ts,.py,.java,.rb"
          # max_comments: 10
          # exclude_patterns: "node_modules/**,dist/**,*.test.js"
```

### Add Required Secrets

- `OPENAI_API_KEY`: Your OpenAI API key with access to GPT-4 or compatible model

The `GITHUB_TOKEN` is automatically provided by GitHub Actions.

## Configuration Options

| Input | Description | Default |
|-------|-------------|---------|
| `github_token` | GitHub token for API access | Required |
| `openai_api_key` | OpenAI API key for code analysis | Required |
| `file_extensions` | File extensions to review (comma-separated) | `.js,.ts,.jsx,.tsx,.py,.java,.go,.rb,.php,.cs` |
| `max_comments` | Maximum number of comments per PR | `10` |
| `exclude_patterns` | File patterns to exclude (comma-separated glob patterns) | `node_modules/**,dist/**,build/**,**/*.min.js` |

## How It Works

1. The action runs when a PR is opened or updated
2. It analyzes the changed files that match the configured file extensions
3. It also examines referenced files (imports, requires) to provide context
4. It uses OpenAI's GPT model to identify potential improvements
5. It posts comments directly on the PR, with explanations and suggested code

## Example Comment

When the action finds an improvement opportunity, it will add a comment like this:

```
**Code Improvement Suggestion:**

This loop can be simplified using list comprehension for better readability and performance.

```suggestion
users = [user for user in all_users if user.is_active]
```
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
