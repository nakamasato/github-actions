#!/usr/bin/env python3
"""Main entry point for the GitHub Action."""

import json
import os
import sys
from typing import Any, Optional

from github import Github


def get_input(name: str, required: bool = False) -> Optional[str]:
    """Get input from GitHub Actions environment."""
    env_var = f"INPUT_{name.upper().replace('-', '_')}"
    value = os.environ.get(env_var, "")
    
    if required and not value:
        error(f"Input required and not supplied: {name}")
        sys.exit(1)
    
    return value if value else None


def set_output(name: str, value: Any) -> None:
    """Set output for GitHub Actions."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{name}={value}\n")
    else:
        # Fallback for older GitHub Actions
        print(f"::set-output name={name}::{value}")


def info(message: str) -> None:
    """Print info message."""
    print(f"::notice::{message}")


def error(message: str) -> None:
    """Print error message."""
    print(f"::error::{message}")


def debug(message: str) -> None:
    """Print debug message."""
    if os.environ.get("ACTIONS_STEP_DEBUG") == "true":
        print(f"::debug::{message}")


def add_to_summary(content: str) -> None:
    """Add content to job summary."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a") as f:
            f.write(content + "\n")


def process_input(example_input: str) -> str:
    """Process the input and return result."""
    # Implement your main logic here
    return f"Processed: {example_input}"


def main() -> None:
    """Main function."""
    try:
        # Get inputs
        example_input = get_input("example-input", required=True)
        github_token = get_input("github-token")
        
        info(f"Processing with input: {example_input}")
        
        # Get GitHub context
        github_context = json.loads(os.environ.get("GITHUB_CONTEXT", "{}"))
        debug(f"Event: {github_context.get('event_name', 'unknown')}")
        
        # Initialize GitHub client if token is provided
        github_client = None
        if github_token:
            github_client = Github(github_token)
        
        # Main logic
        result = process_input(example_input)
        
        # Set outputs
        set_output("result", result)
        set_output("status", "success")
        
        # Add to job summary
        summary = f"""### Action Summary

| Input | Value |
|-------|-------|
| Example Input | {example_input} |
| Result | {result} |
"""
        add_to_summary(summary)
        
        info("Action completed successfully")
        
    except Exception as e:
        error(f"Action failed: {str(e)}")
        if os.environ.get("ACTIONS_STEP_DEBUG") == "true":
            import traceback
            debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()