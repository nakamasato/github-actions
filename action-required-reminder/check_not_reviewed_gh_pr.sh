#!/bin/bash

set -euo pipefail

# 必要な環境変数のチェック
: "${GH_TOKEN:?GH_TOKEN is required}"

# メイン処理
main() {
    local search_query=""

    if [ -n "${GH_REPOS:-}" ]; then
        # GH_REPOSが指定されている場合
        IFS=',' read -ra REPO_ARRAY <<< "$GH_REPOS"
        for repo in "${REPO_ARRAY[@]}"; do
            search_query="${search_query} repo:${repo}"
        done
        search_query="${search_query} state:open --review-requested=@me"
    elif [ -n "${GH_ORG:-}" ]; then
        # GH_ORGが指定されている場合
        search_query="--review-requested=@me \"org:${GH_ORG}\" --state=open"
    else
        # どちらも指定されていない場合はエラー
        echo "Error: Either GH_REPOS or GH_ORG must be specified" >&2
        exit 1
    fi

    # PRを検索してURLのみ出力
    eval "gh search prs ${search_query} --json url --limit 100" | jq -r '.[].url'
}

main
