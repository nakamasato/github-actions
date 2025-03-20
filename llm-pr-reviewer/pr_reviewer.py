#!/usr/bin/env python
import os
import re
import json
import fnmatch
import requests
from openai import OpenAI
from typing import List, Dict, Any

# Configuration from environment
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
FILE_EXTENSIONS = os.getenv("FILE_EXTENSIONS", ".js,.ts,.jsx,.tsx,.py,.java,.go,.rb,.md,.yml,.yaml").split(",")
MAX_COMMENTS = int(os.getenv("MAX_COMMENTS", 5))
EXCLUDE_PATTERNS = os.getenv("EXCLUDE_PATTERNS", "").split(",")
PR_NUMBER = os.environ["PR_NUMBER"]
REPO = os.environ["REPO"]

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

GITHUB_API_URL = f"https://api.github.com/repos/{REPO}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_pr_files() -> List[Dict[str, Any]]:
    """Get the list of files changed in the PR."""
    response = requests.get(
        f"{GITHUB_API_URL}/pulls/{PR_NUMBER}/files",
        headers=HEADERS
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
    if filename.startswith(".github/workflows/") and (filename.endswith(".yml") or filename.endswith(".yaml")):
        return True

    # Check if file has an extension we want to review
    return any(filename.endswith(ext) for ext in FILE_EXTENSIONS)

def get_file_content(filename: str) -> str:
    """Get the content of a file from the repository."""
    response = requests.get(
        f"{GITHUB_API_URL}/contents/{filename}",
        headers=HEADERS,
        params={"ref": f"refs/pull/{PR_NUMBER}/head"}
    )

    if response.status_code == 200:
        content = response.json()["content"]
        import base64
        return base64.b64decode(content).decode('utf-8')
    return ""

def get_referenced_files(file_content: str, filename: str) -> List[str]:
    """Extract referenced files from imports/requires in the code."""
    referenced_files = []

    # Extract file extension and adjust regex patterns based on file type
    ext = os.path.splitext(filename)[1].lower()

    patterns = {
        '.py': [
            r'from\s+(\S+)\s+import',
            r'import\s+(\S+)',
        ],
        '.js': [
            r'import\s+.*\s+from\s+[\'"](.+?)[\'"]',
            r'require\([\'"](.+?)[\'"]\)',
        ],
        '.ts': [
            r'import\s+.*\s+from\s+[\'"](.+?)[\'"]',
            r'import\s+[\'"](.+?)[\'"]',
        ],
        '.go': [
            r'import\s+\(\s*(?:[\'"](.+?)[\'"]\s*)+\s*\)',
            r'import\s+[\'"](.+?)[\'"]',
        ],
        '.java': [
            r'import\s+(.+);',
        ],
        '.rb': [
            r'require\s+[\'"](.+?)[\'"]',
            r'require_relative\s+[\'"](.+?)[\'"]',
        ],
        '.yml': [
            r'uses:\s+(.+?)@',
            r'image:\s+[\'"]?(.+?)[\'"]?$',
        ],
        '.yaml': [
            r'uses:\s+(.+?)@',
            r'image:\s+[\'"]?(.+?)[\'"]?$',
        ],
    }

    # Apply appropriate patterns based on file extension
    ext_patterns = patterns.get(ext, [])
    for pattern in ext_patterns:
        for match in re.finditer(pattern, file_content):
            ref = match.group(1)
            # Convert module references to potential filenames
            if ext == '.py':
                ref = ref.replace('.', '/') + '.py'
            elif ext in ['.js', '.ts']:
                # Handle relative imports
                if not ref.startswith('.'):
                    continue
                if not ref.endswith('.js') and not ref.endswith('.ts'):
                    ref = f"{ref}.{ext[1:]}"
            # Skip external references in GitHub Actions workflows
            elif ext in ['.yml', '.yaml'] and '/' not in ref:
                continue

            # Resolve relative paths
            if ref.startswith('.'):
                base_dir = os.path.dirname(filename)
                ref = os.path.normpath(os.path.join(base_dir, ref))

            if should_review_file(ref):
                referenced_files.append(ref)

    return referenced_files

def analyze_code(changed_content: str, filename: str, referenced_files: Dict[str, str]) -> List[Dict]:
    """Use OpenAI to analyze code and suggest improvements."""
    # Build prompt with context
    prompt = f"""
Analyze the following code from {filename} and suggest specific improvements:

```
{changed_content}
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
    if filename.startswith(".github/workflows/") and (filename.endswith(".yml") or filename.endswith(".yaml")):
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
    "line_start": <number>,
    "line_end": <number>,
    "explanation": "<explanation>",
    "suggestion": "<suggested code>"
  },
  ...
]

Limit to the most important 5 suggestions maximum.
"""

    try:
        # Using the new OpenAI client API format
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a code review assistant. Analyze code and provide specific, helpful improvements as JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )

        # Extract JSON from response
        content = response.choices[0].message.content.strip()
        # Handle case where the response might contain markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\[[\s\S]+?\])\s*```', content)
        if json_match:
            content = json_match.group(1)

        suggestions = json.loads(content)
        return suggestions
    except Exception as e:
        print(f"Error analyzing code: {e}")
        return []

def get_pr_diff_info(pr_number: str) -> Dict[str, Any]:
    """Get PR diff information including commit_id."""
    response = requests.get(
        f"{GITHUB_API_URL}/pulls/{pr_number}",
        headers=HEADERS
    )
    response.raise_for_status()
    pr_data = response.json()
    return {
        "head_sha": pr_data["head"]["sha"],
        "base_sha": pr_data["base"]["sha"]
    }

def post_review_comments(filename: str, suggestions: List[Dict], patch: str) -> None:
    """Post review comments on the PR."""
    # Get PR diff information
    try:
        pr_info = get_pr_diff_info(PR_NUMBER)
        head_sha = pr_info["head_sha"]
    except Exception as e:
        print(f"Error getting PR diff info: {e}")
        return

    # Parse the patch to get position information
    positions = calculate_positions(patch)

    for suggestion in suggestions:
        try:
            # Get the line number from the suggestion
            line_start = suggestion["line_start"]

            # Find the position in the diff
            position = None
            for pos_info in positions:
                if pos_info["line_number"] == line_start:
                    position = pos_info["position"]
                    break

            if position is None:
                print(f"Could not find position for line {line_start} in file {filename}")
                continue

            # Format the comment body
            body = f"**Code Improvement Suggestion:**\n\n{suggestion['explanation']}\n\n"

            # Only include suggestion formatting if there's a clear replacement
            if suggestion.get("suggestion") and len(suggestion["suggestion"].strip()) > 0:
                suggestion_text = suggestion["suggestion"].strip()
                body += f"```suggestion\n{suggestion_text}\n```"

            # Post the comment with required parameters
            comment_data = {
                "body": body,
                "commit_id": head_sha,
                "path": filename,
                "position": position
            }

            try:
                response = requests.post(
                    f"{GITHUB_API_URL}/pulls/{PR_NUMBER}/comments",
                    headers=HEADERS,
                    json=comment_data
                )
                response.raise_for_status()
                print(f"Posted comment on {filename}:{line_start}, position: {position}")
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
                            json=comment_data
                        )
                        response.raise_for_status()
                        print(f"Posted comment without suggestion on {filename}:{line_start}")
                    except requests.exceptions.HTTPError as e:
                        print(f"Still failed to post comment: {e}")
                        print(f"Final response content: {e.response.content.decode('utf-8')}")

        except Exception as e:
            print(f"Error processing suggestion: {e}")

def calculate_positions(patch: str) -> List[Dict[int, int]]:
    """
    Calculate the positions in the diff for each line number.
    Position is a zero-based line index in the entire diff blob.
    """
    if not patch:
        return []

    positions = []
    position_counter = 0  # Zero-based counter for position in the diff
    current_line = 0

    lines = patch.split("\n")

    for line in lines:
        position_counter += 1  # Increment for each line in the diff

        if line.startswith("@@"):
            # Parse the hunk header
            match = re.search(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if match:
                current_line = int(match.group(1)) - 1  # Adjust to 0-based for the next increment
        elif not line.startswith("-"):
            # Only process added or context lines
            current_line += 1
            if line.startswith("+"):
                # This is an added line
                positions.append({
                    "line_number": current_line,
                    "position": position_counter
                })

    return positions

def parse_patch(patch: str) -> Dict[int, int]:
    """Parse the git patch to map file line numbers to PR diff line numbers."""
    if not patch:
        return {}

    line_map = {}
    current_line = 0
    diff_line = 0

    for line in patch.split("\n"):
        if line.startswith("@@"):
            # Parse the hunk header
            match = re.search(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if match:
                hunk_new_start = int(match.group(1))
                current_line = hunk_new_start
                diff_line = 0  # Reset diff line counter for this hunk
        elif not line.startswith("-"):
            # Only process added or context lines (not removed lines)
            if line.startswith("+"):
                # This is an added line
                diff_line += 1
                # For added lines in a brand new file, map the current line to the diff line
                if current_line == 1 and hunk_new_start == 1:
                    line_map[diff_line] = diff_line
                else:
                    line_map[current_line] = diff_line
                current_line += 1
            else:
                # This is a context line
                diff_line += 1
                line_map[current_line] = diff_line
                current_line += 1

    return line_map

def main():
    print("Starting PR code review...")

    # Get files changed in the PR
    pr_files = get_pr_files()
    print(f"Found {len(pr_files)} files to review")

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

        # Analyze the code
        suggestions = analyze_code(file_content, filename, referenced_files)

        # Limit the total number of comments
        remaining_comments = MAX_COMMENTS - comment_count
        if remaining_comments <= 0:
            break

        if len(suggestions) > remaining_comments:
            suggestions = suggestions[:remaining_comments]

        # Post review comments
        if suggestions:
            post_review_comments(filename, suggestions, patch)
            comment_count += len(suggestions)
            print(f"Posted {len(suggestions)} comments for {filename}")

    print(f"PR review completed. Posted {comment_count} comments in total.")

if __name__ == "__main__":
    main()
