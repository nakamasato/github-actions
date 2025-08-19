#!/bin/bash

set -euo pipefail

# Check required environment variables
: "${SLACK_USER_TOKEN:?SLACK_USER_TOKEN is required}"
: "${SLACK_WORKSPACE:?SLACK_WORKSPACE is required}"
: "${SLACK_USER_ID:?SLACK_USER_ID is required}"
: "${SLACK_START_DATE:?SLACK_START_DATE is required}"

# Slack API base URL
SLACK_API_URL="https://slack.com/api"

# Search messages
search_messages() {
    local query="<@${1}> after:${SLACK_START_DATE}"
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
    UNREPLIED_MESSAGES="[]"

    # Debug: Show all messages before filtering
    echo "Debug: All messages from search:" >&2
    echo "$SEARCH_RESULT" | jq '.messages.matches[] | {permalink: .permalink, text: .text[0:100], username: .username, is_private: .channel.is_private}' >&2

    # Filter messages: exclude private channels and ensure text contains the mention
    FILTERED_MESSAGES=$(echo "$SEARCH_RESULT" | jq --arg user_id "@${SLACK_USER_ID}" '[.messages.matches[] | select(.channel.is_private == false and (.text | contains($user_id)))]')

    # Exclude messages from specified usernames if EXCLUDE_SLACK_USERNAMES is set
    if [ -n "${EXCLUDE_SLACK_USERNAMES:-}" ]; then
        echo "Excluding messages from users: $EXCLUDE_SLACK_USERNAMES" >&2
        # Convert newline-separated usernames to JSON array for filtering
        EXCLUDE_USERNAMES_JSON=$(echo "$EXCLUDE_SLACK_USERNAMES" | sed '/^$/d' | jq -R . | jq -s .)
        echo "Exclude usernames JSON: $EXCLUDE_USERNAMES_JSON" >&2

        # Filter out messages from excluded users
        FILTERED_MESSAGES=$(echo "$FILTERED_MESSAGES" | jq --argjson exclude "$EXCLUDE_USERNAMES_JSON" '[.[] | select(.username as $user | ($exclude | index($user) | not))]')
    fi
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
        echo "Processing message $((i + 1)) of $MESSAGE_COUNT" >&2
        MESSAGE=$(echo "$FILTERED_MESSAGES" | jq ".[$i]") || {
            echo "Error: Failed to parse message $i" >&2
            continue
        }
        CHANNEL=$(echo "$MESSAGE" | jq -r '.channel.id')
        TIMESTAMP=$(echo "$MESSAGE" | jq -r '.ts')
        PERMALINK=$(echo "$MESSAGE" | jq -r '.permalink')
        NO_REACTIONS=$(echo "$MESSAGE" | jq -r '.no_reactions // false')
        MESSAGE_TEXT=$(echo "$MESSAGE" | jq -r '.text')

        # Extract text from first 2 blocks
        MESSAGE_BLOCK_TEXT=$(echo "$MESSAGE" | jq -r '[.blocks[0:2][]? | select(.text?.text) | .text.text] | join(" ")' 2>/dev/null || echo "")

        # Debug: Show full message JSON
        echo "Debug: Full message JSON: $MESSAGE" >&2

        # Get thread_ts for threaded messages, otherwise use message ts
        THREAD_TS=$(echo "$PERMALINK" | grep -o 'thread_ts=[0-9.]*' | cut -d'=' -f2) || true
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
            echo "Checking reactions for message $i..." >&2
            if has_user_reaction "$CHANNEL" "$TIMESTAMP" "$SLACK_USER_ID"; then
                HAS_REACTION=true
                REACTED_COUNT=$((REACTED_COUNT + 1))
                echo "Found user reaction" >&2
            fi
        fi

        echo "Checking thread replies for message $i..." >&2
        if has_user_reply_in_thread "$CHANNEL" "$THREAD_ROOT_TS" "$SLACK_USER_ID" "$TIMESTAMP"; then
            HAS_REPLY=true
            REPLIED_COUNT=$((REPLIED_COUNT + 1))
            echo "Found user reply" >&2
        fi

        # Add URL to unreplied list if no reaction or reply
        if [ "$HAS_REACTION" = "false" ] && [ "$HAS_REPLY" = "false" ]; then
            # Debug: Show raw message content
            echo "Debug: Raw MESSAGE_TEXT for $PERMALINK: '$MESSAGE_TEXT'" >&2
            echo "Debug: Raw MESSAGE_BLOCK_TEXT for $PERMALINK: '$MESSAGE_BLOCK_TEXT'" >&2

            # Get first 50 characters - try text field first, then blocks
            if [ -n "$MESSAGE_TEXT" ] && [ "$MESSAGE_TEXT" != "null" ]; then
                MESSAGE_PREVIEW=$(echo "$MESSAGE_TEXT" | head -c 50 | tr '\n' ' ' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
            elif [ -n "$MESSAGE_BLOCK_TEXT" ] && [ "$MESSAGE_BLOCK_TEXT" != "null" ]; then
                MESSAGE_PREVIEW=$(echo "$MESSAGE_BLOCK_TEXT" | head -c 50 | tr '\n' ' ' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
            else
                MESSAGE_PREVIEW=""
            fi

            # If still empty, use channel name as fallback
            if [ -z "$MESSAGE_PREVIEW" ] || [ "${#MESSAGE_PREVIEW}" -lt 3 ]; then
                CHANNEL_NAME=$(echo "$MESSAGE" | jq -r '.channel.name // "unknown"')
                MESSAGE_PREVIEW="Message in #${CHANNEL_NAME}"
            fi

            echo "Debug: MESSAGE_PREVIEW: '$MESSAGE_PREVIEW'" >&2

            # Add to JSON array
            UNREPLIED_MESSAGES=$(echo "$UNREPLIED_MESSAGES" | jq --arg url "$PERMALINK" --arg title "$MESSAGE_PREVIEW" '. + [{"url": $url, "title": $title}]')
        fi
    done

    # Output summary to log
    echo "Messages with emoji reactions: $REACTED_COUNT" >&2
    echo "Messages with thread replies: $REPLIED_COUNT" >&2
    echo "Debug: MESSAGE_COUNT=$MESSAGE_COUNT, REACTED_COUNT=$REACTED_COUNT, REPLIED_COUNT=$REPLIED_COUNT" >&2

    # Output results as JSON
    echo "$UNREPLIED_MESSAGES"
}

main
