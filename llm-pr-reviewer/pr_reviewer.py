#!/usr/bin/env python
import fnmatch
import json
import os
import re
from typing import Any, Dict, List, Set

import requests
from openai import OpenAI

# Configuration from environment
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
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

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

GITHUB_API_URL = f"https://api.github.com/repos/{REPO}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


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
    patch: str,
    file_content: str,
    filename: str,
    referenced_files: Dict[str, str],
) -> List[Dict]:
    """Use OpenAI to analyze code and suggest improvements."""
    # Build prompt with context
    prompt = f"""
Analyze the following code from {filename} and suggest specific improvements:

Patch:
```diff
{patch}
```

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
        prompt += """
For GitHub Actions workflows, focus on:
- Security best practices (e.g., using SHA pinning for actions)
- Performance optimizations (caching, artifact handling)
- Potential race conditions or workflow design issues
- Unnecessary steps or job dependencies
- GitHub Actions specific suggestions
"""
    else:
        prompt += """
Focus on:
- Code quality and best practices
- Performance improvements
- Potential bugs or edge cases
- Security issues
- Readability and maintainability
"""

    prompt += """
Format your response as JSON:
[
  {
    "start_line": <number>,
    "end_line": <number>,
    "explanation": "<explanation>",
    "side": <"LEFT" or "RIGHT" In a split diff view, the side of the diff that the pull request's changes appear on. Can be LEFT or RIGHT. Use LEFT for deletions that appear in red. Use RIGHT for additions that appear in green or unchanged lines that appear in white and are shown for context.>,
    "suggestion": "<suggested code (optional)>",
    "importance": <float between 0.0 and 1.0 indicating how important this suggestion is>,
    "issue_type": "<type of issue: 'bug', 'security', 'performance', 'readability', 'maintainability'>"
  },
  ...
]

Provide a maximum of 10 comments (optionally include suggestion when if you have specific code suggestion), ordered by importance.
For the importance field, use these guidelines:
- 0.9-1.0: Critical issues (security vulnerabilities, serious bugs)
- 0.7-0.9: Important issues (significant performance issues, potential bugs)
- 0.5-0.7: Moderate issues (code quality, maintainability)
- 0.0-0.5: Minor issues (style, readability)

Do not artificially inflate the importance rating.

IMPORTANT: About the "suggestion" field - this will be used with GitHub Pull Request's suggestion feature.
GitHub PR suggestions must contain ONLY the exact code that should replace the lines specified in start_line and end_line.
DO NOT include any explanatory text, comments, or descriptions in the suggestion field - put those in the explanation field instead.

Examples:
1. BAD suggestion: "Change 'actions/checkout@v2' to 'actions/checkout@v3'"
2. GOOD suggestion: "actions/checkout@v3"

If you're not sure about the exact code to suggest, leave the suggestion field empty and only provide an explanation.

IMPORTANT: The start_line and end_line fields must be the lines that are being changed, which means the lines should be between the @@ - and @@ + lines in the patch.
"""

    try:
        # Using the new OpenAI client API format
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a code review assistant. Analyze code and provide specific, helpful improvements as JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        # Extract JSON from response
        content = response.choices[0].message.content.strip()
        # Handle case where the response might contain markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\[[\s\S]+?\])\s*```", content)
        if json_match:
            content = json_match.group(1)

        suggestions = json.loads(content)
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
        print(f"Error getting PR diff info: {e}")
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
            issue_type = suggestion.get("issue_type", "")
            importance = suggestion.get("importance", 0)

            # Add badges for importance and issue type
            badge = ""
            if importance >= 0.9:
                badge = "🔴 **Critical**"
            elif importance >= 0.7:
                badge = "🟠 **Important**"
            elif importance >= 0.5:
                badge = "🟡 **Moderate**"
            else:
                badge = "🟢 **Minor**"

            if issue_type:
                badge += f" | {issue_type.capitalize()}"

            body = f"**Code Improvement Suggestion:** {badge}\n\n{suggestion['explanation']}\n\n"

            # Only include suggestion formatting if there's a clear replacement
            suggestion_text = suggestion.get("suggestion", "").strip()
            if suggestion_text:
                # Check if the suggestion contains any metacharacters or instructions
                meta_patterns = [
                    r"change .+ to",
                    r"replace .+ with",
                    r"use",
                    r"add",
                    r"remove",
                    r"consider",
                    r"should be",
                    r"update",
                ]

                # Only use the suggestion if it doesn't contain explanatory text
                is_valid_code = not any(
                    re.search(pattern, suggestion_text.lower())
                    for pattern in meta_patterns
                )

                if is_valid_code:
                    body += f"```suggestion\n{suggestion_text}\n```"
                else:
                    print(f"Skipping invalid suggestion format: {suggestion_text}")
                    # Use just the explanation without the suggestion block
                    # We could potentially try to extract the actual code from the suggestion
                    # but that would require more complex parsing

            # Post the comment with required parameters
            # https://docs.github.com/en/rest/pulls/comments?apiVersion=2022-11-28#create-a-review-comment-for-a-pull-request
            comment_data = {
                "body": body, # required
                "commit_id": head_sha, # required
                "path": filename, # required
                # "position": position, # deprecated
                "start_line": start_line, # optional needed for multi-line suggestions
                "line": end_line, # end line if multi-line
                "side": side,
                # "start_side": "RIGHT" or "LEFT" # optional
                # "in_reply_to": <review comment id> # optional
                # "subject_type": "file" or "line" # optional
            }

            try:
                response = requests.post(
                    f"{GITHUB_API_URL}/pulls/{PR_NUMBER}/comments",
                    headers=HEADERS,
                    json=comment_data,
                )
                response.raise_for_status()
                comments_posted += 1
                print(
                    f"Posted comment on {filename}:{line_start}, position: {position}"
                )
            except requests.exceptions.HTTPError as e:
                print(f"Error posting comment: {e}")
                print(f"Response content: {e.response.content.decode('utf-8')}")
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
                            f"Posted comment without suggestion on {filename}:{line_start}"
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
    pattern = r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
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


def extract_patch_changes(patch: str) -> List[Dict[int, int]]:
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

    changed_lines = []

    lines = patch.split("\n")

    for line in lines:
        if line.startswith("@@"):
            # Parse the hunk header
            old_start_line, old_end_line, new_start_line, new_end_line = parse_hunk_header(line)
            if old_start_line is not None:
                changed_lines.append(
                    {
                        "old_start_line": old_start_line,
                        "old_end_line": old_end_line,
                        "new_start_line": new_start_line,
                        "new_end_line": new_end_line,
                    }
                )

    return changed_lines


def main():
    print("Starting PR code review...")

    # Get files changed in the PR
    pr_files = get_pr_files()
    print(f"Found {len(pr_files)} files to review")

    # Get existing comments to avoid duplicates
    existing_comments = get_existing_comments()
    print(
        f"Found {sum(len(lines) for lines in existing_comments.values())} existing comment lines"
    )

    comment_count = 0

    for file_info in pr_files:
        filename = file_info["filename"]
        patch = file_info.get("patch", "")

        print(f"Reviewing {filename}")

        # Get the content of the changed file
        file_content = get_file_content(filename)
        if not file_content:
            print(f"Could not retrieve content for {filename}")
            continue

        # Get referenced files
        referenced_files_paths = get_referenced_files(file_content, filename)
        referenced_files = {}
        for ref_path in referenced_files_paths:
            ref_content = get_file_content(ref_path)
            if ref_content:
                referenced_files[ref_path] = ref_content

        # Generate review comments
        review_comments = generate_review_comments(patch, file_content, filename, referenced_files)

        # Limit the total number of comments
        remaining_comments = MAX_COMMENTS - comment_count
        if remaining_comments <= 0:
            print("Reached maximum comment limit. Stopping.")
            break

        # Post review comments (function now handles filtering by importance)
        if review_comments:
            comments_posted = post_review_comments(
                filename, review_comments, existing_comments
            )
            comment_count += comments_posted
            print(f"Posted {comments_posted} comments for {filename}")

    print(f"PR review completed. Posted {comment_count} comments in total.")


if __name__ == "__main__":
    main()
