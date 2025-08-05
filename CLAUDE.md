# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- **JavaScript (pr-description-writer)**:
  - Build: `npm run build` (in pr-description-writer/)
  - Test: `npm test` (runs Jest tests)
  - Single test: `npx jest path/to/test.js`

- **Python (llm-pr-reviewer)**:
  - Install: `poetry install`
  - Test: `poetry run pytest`
  - Single test: `poetry run pytest test_pr_reviwer.py::test_function_name`
  - Lint: `pre-commit run --all-files`

## Code Style Guidelines
- **Python**:
  - Formatting: Use ruff-format (enforced via pre-commit)
  - Linting: Use ruff with auto-fix (enforced via pre-commit)
  - Python version: >= 3.12
  - Imports: Group standard library, third-party, and local imports

- **JavaScript**:
  - Use ES6+ features
  - Format with consistent indentation (2 spaces)
  - Use GitHub Actions toolkit for action development
  - Include unit tests for all new functionality
