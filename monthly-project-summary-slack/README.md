# Monthly Project Summary to Slack Composite Action

月次プロジェクトサマリーを自動生成し、Slackに投稿するcomposite actionです。Claude CodeとMCP（Slack）を使用して、指定されたリポジトリのPRデータを分析し、読みやすい月次活動報告書を生成します。

**クロスorganization対応**: GitHub App tokenを使用することで、他のorganizationのリポジトリにもアクセス可能です。

## 機能

- 指定した月のマージされたPRを自動取得
- Claude CodeによるPRデータの分析とサマリー生成
- カテゴリ別の作業内容整理（機能開発、テスト、インフラなど）
- Slackへの自動投稿（リンク付きPR番号含む）
- 前月を自動選択（手動指定も可能）
- GitHub App token対応でクロスorganizationアクセス可能

## 使用方法

### 基本的な使い方（同一リポジトリ）

```yaml
name: Monthly Project Summary
on:
  schedule:
    - cron: '0 9 1 * *'  # 毎月1日9時に実行
  workflow_dispatch:

jobs:
  generate-summary:
    runs-on: ubuntu-latest
    steps:
      - name: Generate monthly summary
        uses: nakamasato/github-actions/monthly-project-summary-slack@main
        with:
          slack_channel: C1234567890
          slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
          slack_team_id: ${{ secrets.SLACK_TEAM_ID }}
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

### クロスorganization対応（GitHub App token使用）

```yaml
name: Monthly Project Summary
on:
  schedule:
    - cron: '0 9 1 * *'  # 毎月1日9時に実行
  workflow_dispatch:

jobs:
  generate-summary:
    runs-on: ubuntu-latest
    steps:
      - name: Generate GitHub App Token
        id: app-token
        uses: actions/create-github-app-token@v1
        with:
          app-id: ${{ secrets.APP_ID }}
          private-key: ${{ secrets.PRIVATE_KEY }}
          owner: target-org  # アクセス先のorganization

      - name: Generate monthly summary
        uses: nakamasato/github-actions/monthly-project-summary-slack@main
        with:
          repository: target-org/target-repo
          yearmonth: 2024-12
          slack_channel: C1234567890
          timeout_minutes: 10
          github_token: ${{ steps.app-token.outputs.token }}
          slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
          slack_team_id: ${{ secrets.SLACK_TEAM_ID }}
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

## Inputs

| パラメータ | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| `repository` | No | `${{ github.repository }}` | 対象リポジトリ（owner/repo形式） |
| `yearmonth` | No | 前月 | 対象年月（YYYY-MM形式） |
| `slack_channel` | Yes | - | Slack投稿先チャンネルID |
| `timeout_minutes` | No | 5 | Claude Code実行のタイムアウト（分） |
| `github_token` | No | `${{ github.token }}` | GitHub Token（クロスorg用GitHub App token対応） |
| `slack_bot_token` | Yes | - | Slack Bot Token |
| `slack_team_id` | Yes | - | Slack Team ID |
| `claude_code_oauth_token` | No* | - | Claude Code OAuth Token |
| `anthropic_api_key` | No* | - | Anthropic API Key |

*`claude_code_oauth_token`または`anthropic_api_key`のどちらか一つが必要

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

### 基本権限
1. **GitHub Token**: リポジトリの読み取り権限
2. **Slack Bot Token**: チャンネルへの投稿権限
3. **Claude Code**: APIアクセス権限（`claude_code_oauth_token`または`anthropic_api_key`のいずれか一つが必要）

### クロスorganization用GitHub App設定
他のorganizationのリポジトリにアクセスする場合：

1. **GitHub App作成**: 対象organizationでGitHub Appを作成
2. **権限設定**:
   - Repository permissions: `Contents: Read`, `Pull requests: Read`
3. **インストール**: 対象organizationにGitHub Appをインストール
4. **Secrets設定**:
   - `APP_ID`: GitHub AppのID
   - `PRIVATE_KEY`: GitHub Appのprivate key

## エラーハンドリング

処理が失敗した場合、指定されたSlackチャンネルにエラー通知が送信されます。

## 関連

- **Reusable Workflow版**: 同一リポジトリ専用の[reusable-monthly-project-summary-slack](../.github/workflows/reusable-monthly-project-summary-slack.md)もあります
- **違い**: Composite Actionはクロスorganization対応、Reusable Workflowは同一リポジトリのみ対応
