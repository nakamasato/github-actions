#!/usr/bin/env python
import fnmatch
import json
import os
import re
from typing import Any, Dict, List, Set

import requests
from llm_providers import create_llm_provider

# Configuration from environment
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
FILE_EXTENSIONS = os.getenv(
    "FILE_EXTENSIONS", ".js,.ts,.jsx,.tsx,.py,.java,.go,.rb,.md,.yml,.yaml"
).split(",")
MAX_COMMENTS = int(os.getenv("MAX_COMMENTS", 5))
EXCLUDE_PATTERNS = os.getenv("EXCLUDE_PATTERNS", "").split(",")
PR_NUMBER = os.environ["PR_NUMBER"]
REPO = os.environ["REPO"]
COMMENT_THRESHOLD = float(
    os.getenv("COMMENT_THRESHOLD", "0.7")
)  # Threshold for comment importance (0.0-1.0)

# Initialize LLM provider
llm_provider = create_llm_provider()

GITHUB_API_URL = f"https://api.github.com/repos/{REPO}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

CODE_SUGGESTION_INSTRUCTION_PROMPT = """
Format your response as JSON:
[
  {
    "start_line": <number>,
    "end_line": <number>,
    "explanation": "<clear explanation with rationale>",
    "side": <"LEFT" or "RIGHT" In a split diff view, the side of the diff that the pull request's changes appear on. Can be LEFT for deletions that appear in red. Use RIGHT for additions that appear in green or unchanged lines that appear in white and are shown for context.>,
    "suggestion": "<suggested code (optional)>",
    "importance": <float between 0.0 and 1.0 indicating how important this suggestion is>,
    "issue_type": "<type of issue: 'bug', 'security', 'performance', 'readability', 'maintainability', 'design', 'testing'>",
    "confidence": <float between 0.0 and 1.0 indicating confidence in this suggestion>
  },
  ...
]

Provide a maximum of 5 high-quality comments, ordered by importance. Focus on substantive improvements rather than minor style issues unless specifically requested.

For the importance field, use these guidelines:
- 0.9-1.0: Critical issues (security vulnerabilities, serious bugs, data integrity problems)
- 0.7-0.9: Important issues (significant performance issues, potential bugs, maintainability concerns)
- 0.5-0.7: Moderate issues (code quality, design improvements)
- 0.0-0.5: Minor issues (style, readability, documentation)

Include the confidence level for each suggestion to indicate your certainty.

Ensure explanations are:
1. Precise and specific to the code
2. Include the reasoning behind your suggestion
3. Educational - explain the principle behind the improvement
4. Actionable - clear what needs to be changed

IMPORTANT: About the "suggestion" field - this will be used with GitHub Pull Request's suggestion feature.
GitHub PR suggestions must contain ONLY the exact code that should replace the lines specified in start_line and end_line.
DO NOT include any explanatory text, comments, or descriptions in the suggestion field.
If you're not sure about the exact code to suggest, leave the suggestion field empty and only provide an explanation.

CRITICAL: Maintain the EXACT INDENTATION from the original code in your suggestions. The indentation must match perfectly.
Do not use placeholder values like <commit_sha>, <version>, etc. in suggestions - they cannot be directly applied.

IMPORTANT: About the "side" field - this will be used with GitHub Pull Request's suggestion feature.
Use "LEFT" for comments on deletions (with minus signs) that appear in red.
Use "RIGHT" for comments on additions (with plus signs) that appear in green or unchanged lines that appear in white and are shown for context.

IMPORTANT: The start_line and end_line fields MUST ONLY reference lines that were actually changed in the diff (the ones marked with + or - at the beginning).
"""

CODE_TYPE_INSTRUCTION_PROMPT = """
Focus on providing high-value feedback in these areas:

1. Code Quality and Best Practices:
   - SOLID principles violations
   - Design pattern application or misuse
   - Error handling and edge cases
   - Code duplication and reuse opportunities
   - Variable/function naming clarity

2. Performance Issues:
   - Algorithmic inefficiencies (time/space complexity)
   - Resource management (memory, connections, file handles)
   - Unnecessary computations or data structures
   - Database query optimizations

3. Security Concerns:
   - Input validation vulnerabilities
   - Authentication/authorization flaws
   - Data exposure risks
   - Dependency security issues
   - Secure coding practices

4. Maintainability:
   - Test coverage adequacy
   - Documentation completeness
   - Code organization and modularity
   - Future compatibility considerations

Prioritize actionable feedback that will meaningfully improve the codebase.
Limit feedback on trivial stylistic issues unless they significantly impact readability.
"""

GITHUB_ACTIONS_INSTRUCTION_PROMPT = """
For GitHub Actions workflows, focus on:
- Security best practices (e.g., using SHA pinning for actions)
- Performance optimizations (caching, artifact handling)
- Potential race conditions or workflow design issues
- Unnecessary steps or job dependencies
- GitHub Actions specific suggestions
"""


def get_pr_files() -> List[Dict[str, Any]]:
    """Get the list of files changed in the PR."""
    response = requests.get(
        f"{GITHUB_API_URL}/pulls/{PR_NUMBER}/files", headers=HEADERS
    )
    response.raise_for_status()
    return [f for f in response.json() if should_review_file(f["filename"])]


def should_review_file(filename: str) -> bool:
    """Check if the file should be reviewed based on extension, workflow files, and exclude patterns."""
    # Skip files that match exclude patterns
    for pattern in EXCLUDE_PATTERNS:
        if pattern and fnmatch.fnmatch(filename, pattern):
            return False

    # Include GitHub Actions workflow files
    if filename.startswith(".github/workflows/") and (
        filename.endswith(".yml") or filename.endswith(".yaml")
    ):
        return True

    # Check if file has an extension we want to review
    return any(filename.endswith(ext) for ext in FILE_EXTENSIONS)


def get_file_content(filename: str) -> str:
    """Get the content of a file from the repository."""
    response = requests.get(
        f"{GITHUB_API_URL}/contents/{filename}",
        headers=HEADERS,
        params={"ref": f"refs/pull/{PR_NUMBER}/head"},
    )

    if response.status_code == 200:
        content = response.json()["content"]
        import base64

        return base64.b64decode(content).decode("utf-8")
    return ""


def get_referenced_files(file_content: str, filename: str) -> List[str]:
    """Extract referenced files from imports/requires in the code."""
    referenced_files = []

    # Extract file extension and adjust regex patterns based on file type
    ext = os.path.splitext(filename)[1].lower()

    patterns = {
        ".py": [
            r"from\s+(\S+)\s+import",
            r"import\s+(\S+)",
        ],
        ".js": [
            r'import\s+.*\s+from\s+[\'"](.+?)[\'"]',
            r'require\([\'"](.+?)[\'"]\)',
        ],
        ".ts": [
            r'import\s+.*\s+from\s+[\'"](.+?)[\'"]',
            r'import\s+[\'"](.+?)[\'"]',
        ],
        ".go": [
            r'import\s+\(\s*(?:[\'"](.+?)[\'"]\s*)+\s*\)',
            r'import\s+[\'"](.+?)[\'"]',
        ],
        ".java": [
            r"import\s+(.+);",
        ],
        ".rb": [
            r'require\s+[\'"](.+?)[\'"]',
            r'require_relative\s+[\'"](.+?)[\'"]',
        ],
        ".yml": [
            r"uses:\s+(.+?)@",
            r'image:\s+[\'"]?(.+?)[\'"]?$',
        ],
        ".yaml": [
            r"uses:\s+(.+?)@",
            r'image:\s+[\'"]?(.+?)[\'"]?$',
        ],
    }

    # Apply appropriate patterns based on file extension
    ext_patterns = patterns.get(ext, [])
    for pattern in ext_patterns:
        for match in re.finditer(pattern, file_content):
            ref = match.group(1)
            # Convert module references to potential filenames
            if ext == ".py":
                ref = ref.replace(".", "/") + ".py"
            elif ext in [".js", ".ts"]:
                # Handle relative imports
                if not ref.startswith("."):
                    continue
                if not ref.endswith(".js") and not ref.endswith(".ts"):
                    ref = f"{ref}.{ext[1:]}"
            # Skip external references in GitHub Actions workflows
            elif ext in [".yml", ".yaml"] and "/" not in ref:
                continue

            # Resolve relative paths
            if ref.startswith("."):
                base_dir = os.path.dirname(filename)
                ref = os.path.normpath(os.path.join(base_dir, ref))

            if should_review_file(ref):
                referenced_files.append(ref)

    return referenced_files


def generate_review_comments(
    patches: List[Dict[str, str]],
    file_content: str,
    filename: str,
    referenced_files: Dict[str, str],
    temperature: float = 0.2,
    max_tokens: int = 2000,
) -> List[Dict]:
    """Use OpenAI to analyze code and suggest improvements."""
    # Build prompt with context
    prompt = f"""
Analyze the following code from {filename} and suggest specific improvements:
"""
    for i, patch in enumerate(patches):
        prompt += f"""
Patch {i + 1} (old_start_line: {patch["old_start_line"]}, old_end_line: {patch["old_end_line"]}, new_start_line: {patch["new_start_line"]}, new_end_line: {patch["new_end_line"]}):
```
{patch["content_with_line_numbers"]}
```
"""

    prompt += f"""
Entire content of the file:
```
{file_content}
```
"""

    # Add referenced files as context
    if referenced_files:
        prompt += "\nHere are referenced files that might provide context:\n\n"
        for ref_name, ref_content in referenced_files.items():
            # Add a preview of the referenced file (first 20 lines)
            ref_preview = "\n".join(ref_content.split("\n")[:20])
            prompt += f"File {ref_name}:\n```\n{ref_preview}\n...\n```\n\n"

    # Use specific prompt for GitHub Workflows
    if filename.startswith(".github/workflows/") and (
        filename.endswith(".yml") or filename.endswith(".yaml")
    ):
        prompt += GITHUB_ACTIONS_INSTRUCTION_PROMPT
    else:
        prompt += CODE_TYPE_INSTRUCTION_PROMPT
    prompt += CODE_SUGGESTION_INSTRUCTION_PROMPT

    try:
        # Generate review using the LLM provider
        content = llm_provider.generate_review(prompt, temperature, max_tokens)
        # Handle case where the response might contain markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\[[\s\S]+?\])\s*```", content)
        if json_match:
            content = json_match.group(1)

        suggestions = json.loads(content)

        # Filter out low confidence suggestions
        suggestions = [s for s in suggestions if s.get("confidence", 0.5) > 0.4]

        # Sort by importance
        suggestions.sort(key=lambda x: x.get("importance", 0), reverse=True)

        for suggestion in suggestions:
            suggestion["debug_info"] = {
                "prompt": prompt,
                "patches": patches,
                "referenced_files": referenced_files,
                "filename": filename,
                "file_content": file_content,
            }
        return suggestions
    except Exception as e:
        print(f"Error analyzing code: {e}")
        return []


def get_pr_diff_info(pr_number: str) -> Dict[str, Any]:
    """Get PR diff information including commit_id."""
    response = requests.get(f"{GITHUB_API_URL}/pulls/{pr_number}", headers=HEADERS)
    response.raise_for_status()
    pr_data = response.json()
    return {"head_sha": pr_data["head"]["sha"], "base_sha": pr_data["base"]["sha"]}


def get_existing_comments() -> Dict[str, Set[int]]:
    """Get existing bot comments on the PR to avoid duplicates."""
    comments = {}
    page = 1
    while True:
        response = requests.get(
            f"{GITHUB_API_URL}/pulls/{PR_NUMBER}/comments",
            headers=HEADERS,
            params={"page": page, "per_page": 100},
        )
        response.raise_for_status()
        results = response.json()

        if not results:
            break

        for comment in results:
            path = comment["path"]

            # Extract the line number from the comment, handling multiple possible locations
            line = None
            # Try different possible locations for the line number
            if comment.get("line") is not None:
                line = comment["line"]
            elif comment.get("original_line") is not None:
                line = comment["original_line"]
            elif comment.get("position") is not None:
                # Position is fallback, but less accurate
                line = comment["position"]

            # Skip if we couldn't determine a line number
            if line is None:
                continue

            if path not in comments:
                comments[path] = set()

            comments[path].add(line)

        page += 1

    return comments


def post_review_comments(
    filename: str,
    suggestions: List[Dict],
    existing_comments: Dict[str, Set[int]],
) -> int:
    """Post review comments on the PR, avoiding duplicates. Returns the number of comments posted."""
    # Get PR diff information
    try:
        pr_info = get_pr_diff_info(PR_NUMBER)
        head_sha = pr_info["head_sha"]
    except Exception as e:
        print(f"[post_review_comments] Error getting PR diff info: {e}")
        return 0

    # Get lines already commented on for this file
    commented_lines = existing_comments.get(filename, set())

    # Filter out suggestions that are below the importance threshold
    filtered_suggestions = [
        s
        for s in suggestions
        if s.get("importance", 0) >= COMMENT_THRESHOLD
        and s["start_line"] not in commented_lines
    ]

    # Sort by importance (highest first)
    filtered_suggestions.sort(key=lambda x: x.get("importance", 0), reverse=True)

    # Only take the top suggestions
    filtered_suggestions = filtered_suggestions[:MAX_COMMENTS]

    comments_posted = 0
    for suggestion in filtered_suggestions:
        try:
            # Get the line number from the suggestion
            start_line = suggestion["start_line"]
            end_line = suggestion["end_line"]
            side = suggestion["side"]
            # Format the comment body
            issue_type = suggestion.get("issue_type", "").capitalize()
            importance = suggestion.get("importance", 0)
            confidence = suggestion.get("confidence", 0)
            # Add badges for importance and issue type
            if importance >= 0.9:
                severity = "Critical"
                badge_color = "🔴"
            elif importance >= 0.7:
                severity = "Important"
                badge_color = "🟠"
            elif importance >= 0.5:
                severity = "Moderate"
                badge_color = "🟡"
            else:
                severity = "Minor"
                badge_color = "🟢"

            explanation = suggestion["explanation"]

            issue_emoji = {
                "Bug": "🐛",
                "Security": "🔒",
                "Performance": "⚡",
                "Readability": "📖",
                "Maintainability": "🧹",
                "Design": "📐",
                "Testing": "🧪",
            }.get(issue_type, "💡")

            # Build a more informative comment
            body = f"{badge_color} **{severity}** {issue_emoji} **{issue_type}** Suggestion\n\n"

            # Add the explanation with better formatting
            body += f"{explanation}\n\n"

            # Only include suggestion formatting if there's a clear replacement
            suggestion_text = suggestion.get("suggestion", "").strip()
            if suggestion_text and confidence > 0.6:
                # Additional validation of suggestion text
                is_valid_code = not re.search(
                    r"^\s*(change|replace|use|add|remove|consider|should be|update)",
                    suggestion_text.lower(),
                )

                if is_valid_code:
                    body += f"```suggestion\n{suggestion_text}\n```"
                else:
                    print(f"Skipping invalid suggestion format: {suggestion_text}")

            # Post the comment with required parameters
            # https://docs.github.com/en/rest/pulls/comments?apiVersion=2022-11-28#create-a-review-comment-for-a-pull-request
            comment_data = {
                "body": body,  # required
                "commit_id": head_sha,  # required
                "path": filename,  # required
                # "position": position, # deprecated
                "line": end_line,  # line to comment on. end line if multi-line
                "side": side,
                # "start_side": "RIGHT" or "LEFT" # optional
                # "in_reply_to": <review comment id> # optional
                # "subject_type": "file" or "line" # optional
            }
            if start_line != end_line:
                comment_data["start_line"] = (
                    start_line  # optional needed for multi-line suggestions
                )

            is_valid_comment_line = False
            matched_patch = None
            patch_lines = [
                {
                    "start_line": patch["old_start_line"]
                    if side == "LEFT"
                    else patch["new_start_line"],
                    "end_line": patch["old_end_line"]
                    if side == "LEFT"
                    else patch["new_end_line"],
                }
                for patch in suggestion["debug_info"]["patches"]
            ]
            for patch in patch_lines:
                if start_line >= patch["start_line"] and end_line <= patch["end_line"]:
                    is_valid_comment_line = True
                    matched_patch = patch
                    break

            if not is_valid_comment_line:
                print(
                    f"[post_review_comments] Skipping comment on {filename}:{start_line}-{end_line} because it's not in the patch {patch_lines}"
                )
                continue

            comment_metadata = {
                k: v for k, v in comment_data.items() if k not in ["body", "commit_id"]
            }
            print(
                f"[post_review_comments] Comment metadata: {comment_metadata}, matched patch: {matched_patch}, explanation: {suggestion['explanation'][:100]}..."
            )

            try:
                response = requests.post(
                    f"{GITHUB_API_URL}/pulls/{PR_NUMBER}/comments",
                    headers=HEADERS,
                    json=comment_data,
                )
                response.raise_for_status()
                comments_posted += 1
                print(
                    f"[post_review_comments] Posted comment on {filename}:{start_line}-{end_line}"
                )
            except requests.exceptions.HTTPError as e:
                print(f"[post_review_comments] Error posting comment: {e}")
                print(
                    f"[post_review_comments] Response content: {e.response.content.decode('utf-8')}"
                )
                # Try without the suggestion formatting
                if "```suggestion" in body:
                    body = body.split("```suggestion")[0].strip()
                    comment_data["body"] = body
                    try:
                        response = requests.post(
                            f"{GITHUB_API_URL}/pulls/{PR_NUMBER}/comments",
                            headers=HEADERS,
                            json=comment_data,
                        )
                        response.raise_for_status()
                        comments_posted += 1
                        print(
                            f"Posted comment without suggestion on {filename}:{start_line}-{end_line}"
                        )
                    except requests.exceptions.HTTPError as e:
                        print(f"Still failed to post comment: {e}")
                        print(
                            f"Final response content: {e.response.content.decode('utf-8')}"
                        )

        except Exception as e:
            print(f"Error processing suggestion: {e}")

    return comments_posted


def parse_hunk_header(hunk_header):
    """
    Parse a git diff hunk header like '@@ -a,b +c,d @@'
    Returns a tuple of (old_start, old_count, new_start, new_count)
    """
    pattern = r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@"
    match = re.match(pattern, hunk_header)

    if not match:
        return None

    old_start_line = int(match.group(1))
    old_count = int(match.group(2)) if match.group(2) else 1
    new_start_line = int(match.group(3))
    new_count = int(match.group(4)) if match.group(4) else 1
    old_end_line = old_start_line + old_count - 1
    new_end_line = new_start_line + new_count - 1

    return old_start_line, old_end_line, new_start_line, new_end_line


def extract_patch_changes(patch: str) -> List[Dict[str, Any]]:
    """
    Extract patch changes from hunk headers.

    Example:
    ```
    @@ -25,4 +25,5 @@ jobs:
             with:
               working-directory: llm-pr-reviewer
           - name: Run tests
    +        working-directory: llm-pr-reviewer
             run: poetry run pytest
    ```

    Expected output: [{"old_start_line": 25, "old_end_line": 28, "new_start_line": 25, "new_end_line": 29}]
    """
    if not patch:
        return []

    hunks = []
    current_hunk = []
    current_header = None

    lines = patch.split("\n")

    for line in lines:
        if line.startswith("@@"):
            # If we have a current hunk in progress, save it
            if current_hunk and current_header:
                (
                    old_start_line,
                    old_end_line,
                    new_start_line,
                    new_end_line,
                ) = parse_hunk_header(current_header)
                content = "\n".join(current_hunk)

                # Add content with line numbers
                content_with_line_numbers = generate_content_with_line_numbers(
                    current_hunk, old_start_line, new_start_line
                )

                hunks.append(
                    {
                        "header": current_header,
                        "content": content,
                        "content_with_line_numbers": content_with_line_numbers,
                        "old_start_line": old_start_line,
                        "old_end_line": old_end_line,
                        "new_start_line": new_start_line,
                        "new_end_line": new_end_line,
                    }
                )

            # Start a new hunk
            current_header = line
            current_hunk = [line]
        elif current_hunk is not None:
            current_hunk.append(line)

    # Add the last hunk if there is one
    if current_hunk and current_header:
        old_start_line, old_end_line, new_start_line, new_end_line = parse_hunk_header(
            current_header
        )
        content = "\n".join(current_hunk)

        # Add content with line numbers
        content_with_line_numbers = generate_content_with_line_numbers(
            current_hunk, old_start_line, new_start_line
        )

        hunks.append(
            {
                "header": current_header,
                "content": content,
                "content_with_line_numbers": content_with_line_numbers,
                "old_start_line": old_start_line,
                "old_end_line": old_end_line,
                "new_start_line": new_start_line,
                "new_end_line": new_end_line,
            }
        )

    return hunks


def generate_content_with_line_numbers(
    hunk_lines: List[str], old_start: int, new_start: int
) -> str:
    """
    Generate content with line numbers for both left (old) and right (new) sides of the diff.

    Args:
        hunk_lines: Lines of the current hunk
        old_start: Starting line number for old content (left side)
        new_start: Starting line number for new content (right side)

    Returns:
        String with format "OLD_LINE_NUM|NEW_LINE_NUM|CHANGED|CONTENT"
        where CHANGED is 'true' if the line was added or removed, 'false' otherwise
    """
    result = []
    old_line = old_start
    new_line = new_start

    # Skip the hunk header line
    for i in range(1, len(hunk_lines)):
        line = hunk_lines[i]

        if line.startswith("-"):
            # Line only exists in the old version (removed line)
            result.append(f"{old_line}|---|true|{line}")
            old_line += 1
        elif line.startswith("+"):
            # Line only exists in the new version (added line)
            result.append(f"---|{new_line}|true|{line}")
            new_line += 1
        else:
            # Context line that exists in both versions (unchanged)
            result.append(f"{old_line}|{new_line}|false|{line}")
            old_line += 1
            new_line += 1

    return "\n".join(result)


def get_authenticated_user():
    """Get information about the authenticated user (the owner of the token)."""
    response = requests.get("https://api.github.com/user", headers=HEADERS)
    response.raise_for_status()
    return response.json()


def delete_comments():
    """Delete comments authored by the authenticated user."""
    # Get the authenticated user's ID
    user_info = get_authenticated_user()
    authenticated_user_id = user_info["id"]

    print(
        f"[delete_comments] Deleting comments authored by user ID: {authenticated_user_id}"
    )

    # Get all comments on the PR
    all_comments = []
    page = 1
    while True:
        response = requests.get(
            f"{GITHUB_API_URL}/pulls/{PR_NUMBER}/comments",
            headers=HEADERS,
            params={"page": page, "per_page": 100},
        )
        response.raise_for_status()
        results = response.json()

        if not results:
            break

        all_comments.extend(results)
        page += 1

    # Filter comments authored by the authenticated user
    bot_comments = [
        comment
        for comment in all_comments
        if comment["user"]["id"] == authenticated_user_id
    ]

    # Delete each comment
    deleted_count = 0
    for comment in bot_comments:
        comment_id = comment["id"]
        try:
            response = requests.delete(
                f"{GITHUB_API_URL}/pulls/comments/{comment_id}", headers=HEADERS
            )
            response.raise_for_status()
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting comment {comment_id}: {e}")

    print(f"[delete_comments] Deleted {deleted_count} comments")
    return deleted_count


def main():
    print("[main] Starting PR code review...")

    # Get files changed in the PR
    pr_files = get_pr_files()
    print(f"[main] Found {len(pr_files)} files to review")

    # Get existing comments to avoid duplicates
    existing_comments = get_existing_comments()
    print(
        f"[main] Found {sum(len(lines) for lines in existing_comments.values())} existing comment lines"
    )

    comment_count = 0
    check_referenced_files = False
    if DEBUG:
        delete_comments()

    for file_info in pr_files:
        filename = file_info["filename"]
        patch = file_info.get("patch", "")
        patches = extract_patch_changes(patch)

        print(f"[main] Reviewing {filename}")

        # Get the content of the changed file
        file_content = get_file_content(filename)
        if not file_content:
            print(f"[main] Could not retrieve content for {filename}")
            continue

        # Get referenced files
        referenced_files_paths = (
            get_referenced_files(file_content, filename)
            if check_referenced_files
            else []
        )
        referenced_files = {}
        for ref_path in referenced_files_paths:
            ref_content = get_file_content(ref_path)
            if ref_content:
                referenced_files[ref_path] = ref_content

        # Generate review comments
        review_comments = generate_review_comments(
            patches, file_content, filename, referenced_files
        )

        # Limit the total number of comments
        remaining_comments = MAX_COMMENTS - comment_count
        if remaining_comments <= 0:
            print("[main] Reached maximum comment limit. Stopping.")
            break

        # Post review comments (function now handles filtering by importance)
        if review_comments:
            comments_posted = post_review_comments(
                filename, review_comments, existing_comments
            )
            comment_count += comments_posted

    print(f"[main] PR review completed. Posted {comment_count} comments in total.")


if __name__ == "__main__":
    main()
