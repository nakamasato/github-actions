#!/usr/bin/env python
import os
import re
import json
import fnmatch
import requests
import openai
from typing import List, Dict, Any

# Configuration from environment
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
FILE_EXTENSIONS = os.environ["FILE_EXTENSIONS"].split(",")
MAX_COMMENTS = int(os.environ["MAX_COMMENTS"])
EXCLUDE_PATTERNS = os.environ["EXCLUDE_PATTERNS"].split(",")
PR_NUMBER = os.environ["PR_NUMBER"]
REPO = os.environ["REPO"]

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

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
    """Check if the file should be reviewed based on extension and exclude patterns."""
    # Skip files that match exclude patterns
    for pattern in EXCLUDE_PATTERNS:
        if pattern and fnmatch.fnmatch(filename, pattern):
            return False
    
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
    
    prompt += """
Please provide specific code improvement suggestions. For each suggestion:
1. Identify the exact line number(s)
2. Explain why the change is needed
3. Provide the improved code

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

Focus on:
- Code quality and best practices
- Performance improvements
- Potential bugs or edge cases
- Security issues
- Readability and maintainability

Limit to the most important 5 suggestions maximum.
"""

    try:
        response = openai.ChatCompletion.create(
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

def post_review_comments(filename: str, suggestions: List[Dict], patch: str) -> None:
    """Post review comments on the PR."""
    # Parse the patch to map line numbers
    line_map = parse_patch(patch)
    
    for suggestion in suggestions:
        try:
            # Map the line numbers from the file to the PR diff
            line_start = suggestion["line_start"]
            line_pos = line_map.get(line_start)
            
            if not line_pos:
                print(f"Could not map line {line_start} to PR diff for {filename}")
                continue
            
            # Format the comment body
            body = f"**Code Improvement Suggestion:**\n\n{suggestion['explanation']}\n\n"
            
            if suggestion.get("suggestion"):
                body += f"```suggestion\n{suggestion['suggestion']}\n```"
            
            # Post the comment
            comment_data = {
                "body": body,
                "path": filename,
                "line": line_pos,
                "side": "RIGHT"
            }
            
            response = requests.post(
                f"{GITHUB_API_URL}/pulls/{PR_NUMBER}/comments",
                headers=HEADERS,
                json=comment_data
            )
            response.raise_for_status()
            print(f"Posted comment on {filename}:{line_pos}")
            
        except Exception as e:
            print(f"Error posting comment: {e}")

def parse_patch(patch: str) -> Dict[int, int]:
    """Parse the git patch to map file line numbers to PR diff line numbers."""
    if not patch:
        return {}
    
    line_map = {}
    current_line = 0
    hunk_new_start = 0
    
    for line in patch.split("\n"):
        if line.startswith("@@"):
            # Parse the hunk header
            match = re.search(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if match:
                hunk_new_start = int(match.group(1))
                current_line = hunk_new_start - 1
        elif not line.startswith("-"):
            # Only count added or context lines
            current_line += 1
            if not line.startswith("+"):
                # Map file line to diff line for context lines
                line_map[current_line] = current_line
    
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
