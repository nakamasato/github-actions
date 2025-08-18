#!/bin/bash

set -euo pipefail

# Check required environment variables
: "${GH_TOKEN:?GH_TOKEN is required}"

# Main processing
main() {
    local search_query=""

    if [ -n "${GH_REPOS:-}" ]; then
        # When GH_REPOS is specified
        IFS=',' read -ra REPO_ARRAY <<< "$GH_REPOS"
        for repo in "${REPO_ARRAY[@]}"; do
            search_query="${search_query} repo:${repo}"
        done
        search_query="${search_query} state:open --review-requested=@me"
    elif [ -n "${GH_ORG:-}" ]; then
        # When GH_ORG is specified
        search_query="--review-requested=@me \"org:${GH_ORG}\" --state=open"
    else
        # Error if neither is specified
        echo "Error: Either GH_REPOS or GH_ORG must be specified" >&2
        exit 1
    fi

    # Search PRs and output URLs only
    eval "gh search prs ${search_query} --json url --limit 100" | jq -r '.[].url'
}

main
