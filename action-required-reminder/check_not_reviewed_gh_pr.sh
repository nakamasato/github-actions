#!/bin/bash

set -euo pipefail

# Check required environment variables
: "${GH_TOKEN:?GH_TOKEN is required}"
: "${GH_USER:?GH_USER is required}"

# Main processing
main() {
    local search_query=""

    if [ -n "${GH_REPOS:-}" ]; then
        # When GH_REPOS is specified
        IFS=',' read -ra REPO_ARRAY <<< "$GH_REPOS"
        for repo in "${REPO_ARRAY[@]}"; do
            search_query="${search_query} repo:${repo}"
        done
        search_query="${search_query} state:open --review-requested=${GH_USER}"
    elif [ -n "${GH_ORG:-}" ]; then
        # When GH_ORG is specified
        # Try different formats for review-requested
        search_query="\"org:${GH_ORG} review-requested:${GH_USER}\" --state=open"
    else
        # Error if neither is specified
        echo "Error: Either GH_REPOS or GH_ORG must be specified" >&2
        exit 1
    fi

    # Search PRs and output as JSON
    echo "Executing: gh search prs ${search_query} --json url,title --limit 100" >&2

    # First, try without --review-requested to see all PRs in the org
    echo "Debug: Checking all open PRs in org..." >&2
    local all_prs=$(gh search prs "org:datainformed-jp" --state=open --json url,title,reviewRequests --limit 10)
    echo "Debug: Found $(echo "$all_prs" | jq 'length') total open PRs in org" >&2

    # Show review requests for each PR
    echo "$all_prs" | jq -r '.[] | "PR: " + .title + " | Review requests: " + (.reviewRequests | tostring)' >&2

    # Try multiple search patterns
    echo "Debug: Trying different search patterns..." >&2

    # Pattern 1: Original format
    echo "Debug: Pattern 1 - ${search_query}" >&2
    local result1=$(eval "gh search prs ${search_query} --json url,title --limit 100")
    echo "Debug: Pattern 1 found $(echo "$result1" | jq 'length') PRs" >&2

    # Pattern 2: Alternative format
    local alt_query="\"org:datainformed-jp review-requested:${GH_USER} is:open\""
    echo "Debug: Pattern 2 - $alt_query" >&2
    local result2=$(eval "gh search prs $alt_query --json url,title --limit 100")
    echo "Debug: Pattern 2 found $(echo "$result2" | jq 'length') PRs" >&2

    # Pattern 3: Simple format
    local simple_query="org:datainformed-jp review-requested:${GH_USER} is:open"
    echo "Debug: Pattern 3 - $simple_query" >&2
    local result3=$(gh search prs "$simple_query" --json url,title --limit 100)
    echo "Debug: Pattern 3 found $(echo "$result3" | jq 'length') PRs" >&2

    # Use the result with most PRs
    if [ "$(echo "$result3" | jq 'length')" -gt 0 ]; then
        echo "$result3"
    elif [ "$(echo "$result2" | jq 'length')" -gt 0 ]; then
        echo "$result2"
    else
        echo "$result1"
    fi
}

main
