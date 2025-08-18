#!/bin/bash

set -euo pipefail

# Check required environment variables
: "${SLACK_USER_TOKEN:?SLACK_USER_TOKEN is required}"
: "${SLACK_WORKSPACE:?SLACK_WORKSPACE is required}"
: "${SLACK_USER_ID:?SLACK_USER_ID is required}"
: "${SLACK_SEARCH_DAYS:=7}"

# Slack API base URL
SLACK_API_URL="https://slack.com/api"

# Calculate search start date (YYYY-mm-dd format)
SEARCH_FROM=$(date -d "${SLACK_SEARCH_DAYS} days ago" +%Y-%m-%d)

# Search messages
search_messages() {
    local query="<@${1}> after:${SEARCH_FROM}"
    local response=$(curl -s -X GET "${SLACK_API_URL}/search.messages" \
        -H "Authorization: Bearer ${SLACK_USER_TOKEN}" \
        -G \
        --data-urlencode "query=${query}" \
        --data-urlencode "count=100")

    echo "$response"
}

# Check if message has reactions
has_user_reaction() {
    local channel="$1"
    local timestamp="$2"
    local user_id="$3"

    local response=$(curl -s -X GET "${SLACK_API_URL}/reactions.get" \
        -H "Authorization: Bearer ${SLACK_USER_TOKEN}" \
        -G \
        --data-urlencode "channel=${channel}" \
        --data-urlencode "timestamp=${timestamp}")

    if [ "$(echo "$response" | jq -r '.ok')" = "true" ]; then
        # Check if user has reacted
        local reaction_count=$(echo "$response" | jq "[.message.reactions[]?.users[] | select(. == \"${user_id}\")] | length")
        [ "$reaction_count" -gt 0 ]
    else
        false
    fi
}

# Check if user has replied in thread (only replies after mention)
has_user_reply_in_thread() {
    local channel="$1"
    local thread_ts="$2"
    local user_id="$3"
    local mention_ts="$4"

    local response=$(curl -s -X GET "${SLACK_API_URL}/conversations.replies" \
        -H "Authorization: Bearer ${SLACK_USER_TOKEN}" \
        -G \
        --data-urlencode "channel=${channel}" \
        --data-urlencode "ts=${thread_ts}")

    if [ "$(echo "$response" | jq -r '.ok')" = "true" ]; then
        # Check only replies after mention (timestamps after mention message)
        local reply_count=$(echo "$response" | jq "[.messages[] | select(.user == \"${user_id}\" and (.ts | tonumber) > (\"${mention_ts}\" | tonumber))] | length")
        echo "Thread replies after mention: $reply_count" >&2
        [ "$reply_count" -gt 0 ]
    else
        false
    fi
}


# Main processing
main() {
    # Search messages
    SEARCH_RESULT=$(search_messages "$SLACK_USER_ID")

    # Verify search results
    if [ "$(echo "$SEARCH_RESULT" | jq -r '.ok')" != "true" ]; then
        echo "Error: Search failed" >&2
        echo "$SEARCH_RESULT" | jq -r '.error // "Unknown error"' >&2
        exit 1
    fi

    # Process messages from search results
    UNREPLIED_URLS=""

    # Filter to public channels only, excluding private channels
    FILTERED_MESSAGES=$(echo "$SEARCH_RESULT" | jq '[.messages.matches[] | select(.channel.is_private == false)]')
    MESSAGE_COUNT=$(echo "$FILTERED_MESSAGES" | jq 'length')

    echo "Found $MESSAGE_COUNT messages mentioning <@$SLACK_USER_ID> in public channels" >&2

    if [ "$MESSAGE_COUNT" -eq 0 ]; then
        # Exit if no messages found
        exit 0
    fi

    # Initialize counters
    REPLIED_COUNT=0
    REACTED_COUNT=0

    for i in $(seq 0 $((MESSAGE_COUNT - 1))); do
        MESSAGE=$(echo "$FILTERED_MESSAGES" | jq ".[$i]")
        CHANNEL=$(echo "$MESSAGE" | jq -r '.channel.id')
        TIMESTAMP=$(echo "$MESSAGE" | jq -r '.ts')
        PERMALINK=$(echo "$MESSAGE" | jq -r '.permalink')
        NO_REACTIONS=$(echo "$MESSAGE" | jq -r '.no_reactions // false')
        MESSAGE_TEXT=$(echo "$MESSAGE" | jq -r '.text')

        # Get thread_ts for threaded messages, otherwise use message ts
        THREAD_TS=$(echo "$PERMALINK" | grep -o 'thread_ts=[0-9.]*' | cut -d'=' -f2)
        if [ -n "$THREAD_TS" ]; then
            THREAD_ROOT_TS="$THREAD_TS"
        else
            THREAD_ROOT_TS="$TIMESTAMP"
        fi

        echo "Processing message: $(echo "$MESSAGE_TEXT" | head -c 50)... (ts: $TIMESTAMP, thread_ts: $THREAD_ROOT_TS)" >&2

        # Check reactions and thread replies
        HAS_REACTION=false
        HAS_REPLY=false

        # Check reactions only if no_reactions is not true
        if [ "$NO_REACTIONS" != "true" ]; then
            if has_user_reaction "$CHANNEL" "$TIMESTAMP" "$SLACK_USER_ID"; then
                HAS_REACTION=true
                REACTED_COUNT=$((REACTED_COUNT + 1))
            fi
        fi

        if has_user_reply_in_thread "$CHANNEL" "$THREAD_ROOT_TS" "$SLACK_USER_ID" "$TIMESTAMP"; then
            HAS_REPLY=true
            REPLIED_COUNT=$((REPLIED_COUNT + 1))
        fi

        # Add URL to unreplied list if no reaction or reply
        if [ "$HAS_REACTION" = "false" ] && [ "$HAS_REPLY" = "false" ]; then
            if [ -n "$UNREPLIED_URLS" ]; then
                UNREPLIED_URLS="${UNREPLIED_URLS}\n${PERMALINK}"
            else
                UNREPLIED_URLS="${PERMALINK}"
            fi
        fi
    done

    # Output summary to log
    echo "Messages with emoji reactions: $REACTED_COUNT" >&2
    echo "Messages with thread replies: $REPLIED_COUNT" >&2
    UNREPLIED_COUNT=$((MESSAGE_COUNT - REACTED_COUNT - REPLIED_COUNT))
    echo "Unreplied messages: $UNREPLIED_COUNT" >&2

    # Output results
    if [ -n "$UNREPLIED_URLS" ]; then
        echo -e "$UNREPLIED_URLS"
    fi
}

main
