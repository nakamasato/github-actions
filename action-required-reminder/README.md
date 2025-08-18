# Action Required Reminder

GitHub Action that checks for unreplied Slack messages and unreviewed GitHub PRs, then sends a reminder to Slack.

## Features

- 🔍 Searches for Slack messages where you're mentioned
- 📬 Identifies messages without emoji reactions or thread replies
- 🔎 Finds GitHub PRs where you're requested as a reviewer
- 📝 Checks if you've already reviewed the PRs
- 📢 Sends a consolidated reminder to Slack

## Usage

```yaml
name: Action Required Reminder
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at 9 AM JST
  workflow_dispatch:

jobs:
  remind:
    runs-on: ubuntu-latest
    steps:
      - uses: nakamasato/github-actions/action-required-reminder@main
        with:
          slack_workspace: 'your-workspace'
          slack_channel_id: ${{ secrets.SLACK_CHANNEL_ID }}
          slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
          slack_user_id: 'U1234567890'
          github_token: ${{ secrets.GITHUB_TOKEN }}
          # Optional: specify repositories
          gh_repos: 'owner/repo1,owner/repo2'
          # Or specify organization (ignored if gh_repos is set)
          gh_org: 'your-org'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `gh_org` | Target GitHub organization | No | - |
| `gh_repos` | Target repositories (comma-separated) | No | - |
| `slack_workspace` | Slack workspace name | Yes | - |
| `slack_channel_id` | Slack channel ID for reminders | Yes | - |
| `slack_bot_token` | Slack Bot Token | Yes | - |
| `slack_search_days` | Days to search for Slack messages | No | `7` |
| `slack_user_id` | Target Slack user ID | Yes | - |
| `github_token` | GitHub Token | No | `${{ github.token }}` |

## Slack Bot Setup

Your Slack bot needs the following OAuth scopes:
- `channels:history` - Access messages in public channels
- `channels:read` - View basic channel information
- `chat:write` - Send messages
- `reactions:read` - View emoji reactions
- `search:read` - Search messages
- `users:read` - View user information

## Examples

### Check specific repositories

```yaml
- uses: nakamasato/github-actions/action-required-reminder@main
  with:
    gh_repos: 'myorg/frontend,myorg/backend,myorg/docs'
    slack_workspace: 'your-workspace'
    slack_channel_id: 'C1234567890'
    slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
    slack_user_id: 'U1234567890'
```

### Check all repositories in an organization

```yaml
- uses: nakamasato/github-actions/action-required-reminder@main
  with:
    gh_org: 'myorg'
    slack_workspace: 'your-workspace'
    slack_channel_id: 'C1234567890'
    slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
    slack_user_id: 'U1234567890'
```

### Custom search period

```yaml
- uses: nakamasato/github-actions/action-required-reminder@main
  with:
    slack_workspace: 'your-workspace'
    slack_channel_id: 'C1234567890'
    slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
    slack_user_id: 'U1234567890'
    slack_search_days: '14'  # Check last 2 weeks
```

## Output Example

The action posts a message to Slack like:

```
👋 <@U1234567890> さん、要アクションリマインダーです！

📬 未返信のSlackメッセージ: 3件
https://workspace.slack.com/archives/C123/p1234567890
https://workspace.slack.com/archives/C456/p1234567891
https://workspace.slack.com/archives/C789/p1234567892

🔍 レビュー待ちのPR: 2件
https://github.com/myorg/frontend/pull/123
https://github.com/myorg/backend/pull/456

今日も頑張りましょう！💪
```
