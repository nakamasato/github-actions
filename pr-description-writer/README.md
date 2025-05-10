# PR Description Writer

A GitHub Action that automatically generates Pull Request descriptions based on code changes.

## Motivation

[pr-agent](https://github.com/qodo-ai/pr-agent) only provides [marker-template](https://qodo-merge-docs.qodo.ai/tools/describe/?h=marker#markers-template)([pr-agent#273](https://github.com/qodo-ai/pr-agent/pull/273)) and doesn't support [pull request template](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository) ([pr-agent#213](https://github.com/qodo-ai/pr-agent/issues/213)).

With this GitHub Actions, you can configure how to generate PR descriptions more flexibly.

## Features

- Analyzes changed files in a PR to understand the code changes
- Uses OpenAI or Anthropic LLMs to generate meaningful PR descriptions
- Supports custom PR templates
- Can learn from example PRs to match your team's style
- Allows custom prompt instructions
- Update PR description

## Usage

Add this action to your GitHub workflow:

```yaml
name: Generate PR Description

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  generate-description:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Generate PR Description
        uses: nakamasato/github-actions/pr-description-writer@v1.10.1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          # anthropic config
          llm_provider: anthropic
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          anthropic_model: claude-3-opus-20240229
          # openai config
          # llm_provider: openai
          # openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          # openai_model: gpt-4o-mini
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

### Example Custom Prompt (pr_prompt.txt)

Here's an example of a custom prompt file in Japanese for conventional commit style PRs:

```
以下の指示に従ってPull Requestの説明を生成してください：

1. description:
    - 基本はWhatとWhyのセクション (## What と ## Why)を簡潔にわかりやすく
    - WhatもWhyもともにリスト形式
    - What
        - 変更点は箇条書き
        - リストの数は多くなりすぎないように、2,3個がベスト. Max5個
        - リストの数が多い場合は、リストの階層を使ってわかりやすくする (マックス階層の深さ2)
    - 破壊的変更がある場合は目立つように記載してください (ある場合のみ ## Breaking Changes を追加)
    - 関連するチケットやIssueがある場合はリンクしてください (ある場合のみ ## Related Issuesを追加)
    - 絵文字は適度に使用してOKです（特に見出しの前など）
```

## Example PR Template

This action works best when you have a structured PR template:

```markdown
## What

<!-- Brief description of what this PR does -->

## Why

<!-- Explain the context and motivation for this change -->
```

## Building the Action

```bash
npm install
npm run build
```

## Test

```bash
npm test
```

## License

MIT
