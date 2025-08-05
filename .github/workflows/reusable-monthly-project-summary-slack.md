# Monthly Project Summary Slack Reusable Workflow

月次プロジェクトサマリーを自動生成し、Slackに投稿する再利用可能なGitHub Actionsワークフローです。AIとMCP（Slack）を使用して、指定されたリポジトリのPRデータを分析し、読みやすい月次活動報告書を生成します。

## 機能

- 指定した月のマージされたPRを自動取得
- AIによるPRデータの分析とサマリー生成
- カテゴリ別の作業内容整理（機能開発、テスト、インフラなど）
- Slackへの自動投稿（リンク付きPR番号含む）
- 前月を自動選択（手動指定も可能）

## 使用方法

他のリポジトリから以下のように呼び出します：

```yaml
name: Monthly Project Summary
on:
  schedule:
    - cron: '0 9 1 * *'  # 毎月1日9時に実行
  workflow_dispatch:

jobs:
  generate-summary:
    uses: nakamasato/github-actions/.github/workflows/reusable-monthly-project-summary-slack.yml@main
    with:
      repository: owner/repo  # オプション：未指定時は現在のリポジトリ
      yearmonth: 2024-12     # オプション：未指定時は前月
      slack_channel: C1234567890
      timeout_minutes: 10    # オプション：未指定時は5分
    secrets:
      slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
      slack_team_id: ${{ secrets.SLACK_TEAM_ID }}
      github_token: ${{ secrets.GITHUB_TOKEN }}
      claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}  # どちらか一つが必要
      anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}  # どちらか一つが必要
```

## パラメータ

### Inputs

| パラメータ | 必須 | 説明 |
|-----------|------|------|
| `repository` | No | 対象リポジトリ（owner/repo形式）。未指定時は現在のリポジトリ |
| `yearmonth` | No | 対象年月（YYYY-MM形式）。未指定時は前月 |
| `slack_channel` | Yes | Slack投稿先チャンネルID |
| `timeout_minutes` | No | AI実行のタイムアウト（分）。デフォルト5分 |

### Secrets

| シークレット | 必須 | 説明 |
|-------------|------|------|
| `slack_bot_token` | Yes | Slack Bot Token |
| `slack_team_id` | Yes | Slack Team ID |
| `github_token` | Yes | GitHub Token（PR取得用） |
| `claude_code_oauth_token` | No* | Claude Code OAuth Token |
| `anthropic_api_key` | No* | Anthropic API Key |

*どちらか一つが必要

## 生成されるサマリー形式

```
12月もお疲れ様です！ repository-name 活動サマリーです。合計15のPRがマージされました!

*機能開発*
• ユーザー認証機能の追加 (#123, #125)
• API レスポンス形式の改善 (#130)

*テスト・品質向上*
• テストカバレッジの向上 (#135, #140)
• リファクタリング作業 (#145)

*インフラ・運用*
• CI/CDパイプラインの改善 (#150)

今月も素晴らしい成果です！来月も頑張りましょう！
```

## 必要な権限・設定

1. **GitHub Token**: リポジトリの読み取り権限
2. **Slack Bot Token**: チャンネルへの投稿権限
3. **AI API**: APIアクセス権限（`claude_code_oauth_token`または`anthropic_api_key`のいずれか一つが必要）

## タイムアウト

- ワークフロー全体: 30分
- AI実行: デフォルト5分（`timeout_minutes`パラメータで調整可能）

## エラーハンドリング

処理が失敗した場合、指定されたSlackチャンネルにエラー通知が送信されます。