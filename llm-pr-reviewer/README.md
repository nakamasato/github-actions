# LLM PR Reviewer

> [!NOTE]
> This GitHub Actions is still alpha version.

A GitHub Action that automatically reviews Pull Requests and adds helpful code improvement suggestions as comments using an LLM (Large Language Model).

## Features

- Analyzes code changes in PRs and suggests improvements
- Comments directly on the specific lines that need attention
- Provides context-aware suggestions by examining referenced files
- Customizable file extensions and exclusion patterns
- Limits the number of comments to avoid overwhelming reviewers
- Suggests improvements with explanatory comments and code suggestions
- Supports multiple LLM providers (OpenAI and Anthropic)

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
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: LLM PR Reviewer
        uses: nakamasato/github-actions/llm-pr-reviewer@latest
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          # Choose your LLM provider:
          llm_provider: openai  # or 'anthropic'
          # Provider-specific configurations:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}  # Required if using OpenAI
          # anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}  # Required if using Anthropic
          # Optional configurations:
          # file_extensions: ".js,.ts,.py,.java,.rb"
          # max_comments: 10
          # exclude_patterns: "node_modules/**,dist/**,*.test.js"
```

### Add Required Secrets

- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI)
- `ANTHROPIC_API_KEY`: Your Anthropic API key (if using Anthropic)

The `GITHUB_TOKEN` is automatically provided by GitHub Actions.

## Configuration Options

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `github_token` | GitHub token for API access | Yes | N/A |
| `llm_provider` | LLM provider to use (`openai` or `anthropic`) | No | `openai` |
| `openai_api_key` | OpenAI API key | No* | N/A |
| `openai_model` | OpenAI model to use | No | `gpt-4-turbo-preview` |
| `anthropic_api_key` | Anthropic API key | No* | N/A |
| `anthropic_model` | Anthropic model to use | No | `claude-3-opus-20240229` |
| `file_extensions` | File extensions to review (comma-separated) | No | `.js,.ts,.jsx,.tsx,.py,.java,.go,.rb,.php,.cs` |
| `max_comments` | Maximum number of comments per PR | No | `10` |
| `exclude_patterns` | File patterns to exclude (comma-separated glob patterns) | No | `node_modules/**,dist/**,build/**,**/*.min.js` |
| `debug` | Debug mode. If true, the bot will delete its own comments before posting new ones. The bot will also print debug information to the comments. Currently not available ❌️ (fail to get https://api.github.com/user) | No | `false` |

*Either `openai_api_key` or `anthropic_api_key` is required depending on the chosen `llm_provider`.

## How It Works

1. The action runs when a PR is opened or updated
2. It analyzes the changed files that match the configured file extensions
3. It also examines referenced files (imports, requires) to provide context
4. It uses the configured LLM provider to identify potential improvements
5. It posts comments directly on the PR, with explanations and suggested code

## Example Comment

When the action finds an improvement opportunity, it will add a comment like this:

````
**Code Improvement Suggestion:**

This loop can be simplified using list comprehension for better readability and performance.

```suggestion
users = [user for user in all_users if user.is_active]
```
````

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

You can run the script on your local:

```
DEBUG=true GITHUB_TOKEN=$(gh auth token) REPO=<owner>/<repo> PR_NUMBER=<pr number> LLM_PROVIDER=openai OPENAI_API_KEY=<your-key> poetry run python pr_reviewer.py
# Or for Anthropic:
# DEBUG=true GITHUB_TOKEN=$(gh auth token) REPO=<owner>/<repo> PR_NUMBER=<pr number> LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=<your-key> poetry run python pr_reviewer.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
